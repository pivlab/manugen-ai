# 1) Install required packages (run once in your environment)
#    !pip install duckdb transformers FlagEmbedding polars

import duckdb
import numpy as np
import pyarrow as pa
import torch
from FlagEmbedding import BGEM3FlagModel
import logging
import pathlib

# avoid warnings from transformers
logging.getLogger("transformers").setLevel(logging.ERROR)

# set device and model for data work
DEVICE = "cuda" if torch.cuda.is_available() else \
          "mps"  if torch.backends.mps.is_available() else "cpu"
EMBEDDING_MODEL = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, device=DEVICE)

def embed(text: str) -> np.ndarray:
    """
    Generate a dense vector embedding for the given text using the model.

    Args:
        text (str):
          The input text to embed.

    Returns:
        np.ndarray:
          The dense vector representation of the input text as a NumPy array of type float32.

    Example:
        >>> vec = embed("Hello world")
        >>> vec.shape
        (768,)
    """
    vec = EMBEDDING_MODEL.encode([text], batch_size=4)["dense_vecs"][0]
    return vec.astype(np.float32)


def create_withdrarxiv_embeddings(target_db: str = "withdrarxiv_embeddings.duckdb", ) -> str:
  """
  Create and store vector embeddings for the withdrarxiv dataset in a
  DuckDB database.

  This function loads paper metadata from a Parquet file, filters out
  certain categories, computes dense vector embeddings for each abstract
  using a FlagEmbedding model, and stores the results in a DuckDB
  database. Embeddings are computed in batches and stored in a separate
  table for efficient retrieval and similarity search.

  Args:
      target_db (str, optional): Path to the DuckDB database where
          embeddings will be stored. Defaults to
          "src/manugen_ai/data/withdrarxiv_embeddings.duckdb".

  Returns:
      str: The path to the DuckDB database containing the paper metadata
          and embeddings.

  Notes:
      - The Parquet data must be downloaded manually due to Hugging Face
        download restrictions.
      - Download link:
        https://huggingface.co/datasets/darpa-scify/withdrarxiv/
      - Only papers not in the categories 'subsumed by another
        publication' or 'reason not specified' are included.
      - Embeddings are computed using the BAAI/bge-m3 model with device
        auto-detection.

  Example:
      >>> db_path = create_withdrarxiv_embeddings()
      >>> print(f"Embeddings stored in: {db_path}")
    """
  # Connect to (or create) your DuckDB database
  conn = duckdb.connect(str(pathlib.Path(__file__).parent / "data" / target_db))

  # The data are preloaded manually due to download restrictions
  # from huggingface.
  # Download is available from:
  # https://huggingface.co/datasets/darpa-scify/withdrarxiv/
  # resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet?download=true
  parquet_path = str(pathlib.Path(__file__).parent / "data" / "withdrarxiv.parquet")

  # Create a DuckDB table "papers" from your Parquet
  conn.execute(f"""
  CREATE OR REPLACE TABLE papers AS
  SELECT
    arxiv_id,
    title,
    abstract,
    subjects,
    scrubbed_comments,
    category
  FROM read_parquet('{parquet_path}')
  WHERE category not in 
    ('subsumed by another publication',
    'reason not specified')
  """)

  # Load the FlagEmbedding model (or swap in your own)
  device = "cuda" if torch.cuda.is_available() else \
          "mps"  if torch.backends.mps.is_available() else "cpu"
  model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, device=device)

  conn.execute("""
  CREATE OR REPLACE TABLE embeddings (
    arxiv_id VARCHAR,
    embedding FLOAT[1024]
  );
  """)

  conn.create_function("embed", embed, [duckdb.typing.VARCHAR], "FLOAT[1024]")

  # Batch-compute embeddings for every abstract
  batch_size = 100
  conn.cursor()
  while True:
    batch_table = conn.execute(f"""
        SELECT arxiv_id, abstract
        FROM papers
        WHERE arxiv_id NOT IN (SELECT arxiv_id FROM embeddings)
        LIMIT {batch_size}
    """).fetch_arrow_table()

    if batch_table.num_rows == 0:
        break

    texts = batch_table['abstract'].to_pylist()
    embs  = EMBEDDING_MODEL.encode(texts, batch_size=4)["dense_vecs"].astype(np.float32)

    embedding_column = pa.array(embs.tolist(), type=pa.list_(pa.float32()))
    batch_with_emb = batch_table.append_column("embedding", embedding_column)

    # Register and insert only id + embedding
    conn.register("batch", batch_with_emb)
    conn.execute("""
        INSERT INTO embeddings
        SELECT arxiv_id, embedding
        FROM batch
    """)
    conn.unregister("batch")

  # ensure we close the connection
  conn.close()

  # return the target database path
  return target_db

# Define a helper to search top-k papers by abstract similarity
def search_withdrarxiv_embeddings(query: str, top_k: int = 2):
    """
    Search for papers related to a given abstract query using vector similarity.

    Args:
        query (str):
          The abstract or query string to
          search for similar papers.
        top_k (int, optional):
          The number of top similar papers to return.
          Defaults to 2.

    Returns:
        Dict[str, str]:
          A dictionary containing the related
          retraction reasons for the top matching papers.

    Example:
        >>> df = search_abstract("deep learning for protein folding", top_k=3)
        >>> print(df.head())
    """


    target_db = str(pathlib.Path(__file__).parent / "data" / "withdrarxiv_embeddings.duckdb")

    conn = duckdb.connect(target_db)
    conn.create_function("embed", embed, [duckdb.typing.VARCHAR], "FLOAT[1024]")

    q = {"q": query, "k": top_k}
    df = conn.execute("""
      WITH topk AS (
        SELECT
          arxiv_id,
          array_inner_product(embedding, embed($q)) AS similarity
        FROM embeddings
        ORDER BY similarity DESC
        LIMIT $k
      )
      SELECT
        p.scrubbed_comments as related_retraction_reasons
      FROM topk
      JOIN papers p USING(arxiv_id)
      ORDER BY similarity DESC;
      """, q).df().to_json(orient="records")
    conn.close()
    return df
