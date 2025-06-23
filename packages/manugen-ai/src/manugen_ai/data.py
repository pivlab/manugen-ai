# 1) Install required packages (run once in your environment)
#    !pip install duckdb transformers FlagEmbedding polars

import logging
import os
import pathlib

import duckdb
import numpy as np
import pyarrow as pa

from manugen_ai.utils import download_file_if_not_available

# if USE_GEMINI_EMBEDDINGS is 1, we'll use
USE_GEMINI_EMBEDDINGS = os.environ.get("USE_GEMINI_EMBEDDINGS", "1") == "1"

# ----------------------------------------------------
# --- Gemini embeddings setup
# ----------------------------------------------------

GEMINI_EMBEDDING_MODEL_NAME = os.environ.get(
    "GEMINI_EMBEDDING_MODEL_NAME", "gemini-embedding-exp-03-07"
)

# singleton for the google genai client
# set the first time get_genai_client() is called
_GENAI_CLIENT = None


def get_genai_client():
    """
    Get the Google GenAI client for generating embeddings.

    This function initializes the GenAI client if it has not been
    created yet, ensuring that the client is loaded only once and reused
    across calls.

    Returns:
        google.genai.client: The initialized GenAI client.
    """
    global _GENAI_CLIENT

    if _GENAI_CLIENT is None:
        from google import genai

        # initialize the GenAI client
        _GENAI_CLIENT = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    return _GENAI_CLIENT


# ----------------------------------------------------
# --- FlagEmbedding embeddings setup
# ----------------------------------------------------

FLAGEMBEDDING_MODEL_OR_PATH = os.environ.get(
    "FLAGEMBEDDING_MODEL_OR_PATH", "BAAI/bge-m3"
)
FLAGEMBEDDING_CACHE_DIR = os.environ.get("FLAGEMBEDDING_CACHE_DIR", "/opt/model_cache/")

# singleton for the flagembedding model
# set the first time get_flag_embedding_model() is called
_EMBEDDING_MODEL = None


def get_flag_embedding_model():
    """
    Get the FlagEmbedding model for generating dense vector embeddings.

    This function initializes the embedding model if it has not been
    created yet, ensuring that the model is loaded only once and reused
    across calls.

    Returns:
        BGEM3FlagModel: The initialized embedding model.
    """
    global _EMBEDDING_MODEL

    if _EMBEDDING_MODEL is None:
        # import these here, as they're only needed when we're using BGE-M3
        import torch
        from FlagEmbedding import BGEM3FlagModel

        # avoid warnings from transformers
        logging.getLogger("transformers").setLevel(logging.ERROR)

        # set device and model for data work
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        _EMBEDDING_MODEL = BGEM3FlagModel(
            FLAGEMBEDDING_MODEL_OR_PATH,
            cache_dir=FLAGEMBEDDING_CACHE_DIR,
            use_fp16=True,
            device=device,
        )

    return _EMBEDDING_MODEL


# ----------------------------------------------------
# --- General Withdrarxiv Encoding and Search
# ----------------------------------------------------


def get_model_name() -> str:
    """
    Get the name of the embedding model being used.
    """
    if USE_GEMINI_EMBEDDINGS:
        # use the gemini model name
        return GEMINI_EMBEDDING_MODEL_NAME
    else:
        # Extract model name from path
        return FLAGEMBEDDING_MODEL_OR_PATH.split("/")[-1]


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
    if USE_GEMINI_EMBEDDINGS:
        embeddings = (
            get_genai_client()
            .models.embed_content(model=GEMINI_EMBEDDING_MODEL_NAME, contents=[text])
            .embeddings[0]
            .values
        )

        vec = np.array(embeddings, dtype=np.float32)
    else:
        vec = get_flag_embedding_model().encode([text], batch_size=4)["dense_vecs"][0]

    return vec.astype(np.float32)


def embed_batch(texts: list[str]) -> np.ndarray:
    """
    Generate dense vector embeddings for a batch of texts.

    Args:
        texts (list[str]):
          A list of input texts to embed.

    Returns:
        np.ndarray:
          A NumPy array of shape (n, 1024) containing the dense vector representations
          of the input texts, where n is the number of texts.

    Example:
        >>> vecs = embed_batch(["Hello world", "Another text"])
        >>> vecs.shape
        (2, 1024)
    """
    if USE_GEMINI_EMBEDDINGS:
        embeddings = [
            x.values
            for x in get_genai_client()
            .models.embed_content(model=GEMINI_EMBEDDING_MODEL_NAME, contents=texts)
            .embeddings
        ]
        embs = np.array(embeddings, dtype=np.float32)
    else:
        embs = get_flag_embedding_model().encode(texts, batch_size=4)["dense_vecs"]

    return embs.astype(np.float32)


def get_embedding_size() -> int:
    """
    Get the size of the dense vector embeddings.

    BAAI/bge-m3 embeddings have 1024 components ,
    while Gemini embeddings have 768.

    Returns:
        int: The size of the dense vector embeddings,
    """
    return 768 if USE_GEMINI_EMBEDDINGS else 1024


def create_withdrarxiv_embeddings(
    target_db: str = "withdrarxiv_embeddings.duckdb",
) -> str:
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

    if target_db is None:
        target_db = f"withdrarxiv_embeddings_{get_model_name()}.duckdb"

    # Connect to (or create) your DuckDB database
    conn = duckdb.connect(str(pathlib.Path(__file__).parent / "data" / target_db))

    # The data are preloaded manually due to download restrictions
    # from huggingface.
    # Download is available from:
    # https://huggingface.co/datasets/darpa-scify/withdrarxiv/
    # resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet?download=true
    parquet_path = str(pathlib.Path(__file__).parent / "data" / "withdrarxiv.parquet")

    # Create a DuckDB table "papers" from your Parquet
    conn.execute(
        f"""
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
        """
    )

    conn.execute(
        f"""
        CREATE OR REPLACE TABLE embeddings (
          arxiv_id VARCHAR,
          embedding FLOAT[{get_embedding_size()}]
        );
        """
    )

    conn.create_function(
        "embed", embed, [duckdb.typing.VARCHAR], f"FLOAT[{get_embedding_size()}]"
    )

    # Batch-compute embeddings for every abstract
    batch_size = 100
    conn.cursor()
    while True:
        batch_table = conn.execute(
            f"""
        SELECT arxiv_id, abstract
        FROM papers
        WHERE arxiv_id NOT IN (SELECT arxiv_id FROM embeddings)
        LIMIT {batch_size}
        """
        ).fetch_arrow_table()

        if batch_table.num_rows == 0:
            break

        texts = batch_table["abstract"].to_pylist()
        embs = embed_batch(texts)

        embedding_column = pa.array(embs.tolist(), type=pa.list_(pa.float32()))
        batch_with_emb = batch_table.append_column("embedding", embedding_column)

        # Register and insert only id + embedding
        conn.register("batch", batch_with_emb)
        conn.execute(
            """
        INSERT INTO embeddings
        SELECT arxiv_id, embedding
        FROM batch
        """
        )
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

    # retrieve a precomputed embeddings database based on the model we're using
    model_name = get_model_name()

    if model_name == "text-embedding-004":
        src_url = "https://olucdenver-my.sharepoint.com/:u:/g/personal/dave_bunten_cuanschutz_edu/EUxMDRvp-zZInkE5NqNYz0ABIkKtOO-5DFIrkBeVbi_p_A?download=1"
    elif model_name == "bge-m3":
        src_url = (
            "https://olucdenver-my.sharepoint.com/:u:"
            "/g/personal/dav"
            "e_bunten_cuansc"
            "hutz_edu/EdC8fHAME2dLm5G9A"
            "xtVbL0B7EAf4cWF3XCXwZTPYNWa2A?download=1"
        )
    else:
        raise Exception(
            f"No embeddings file exists for model {model_name}, please run the embedding creation first."
        )

    # construct path to the DuckDB database
    target_db_path = str(
        pathlib.Path(__file__).parent
        / "data"
        / f"withdrarxiv_embeddings_{model_name}.duckdb"
    )

    target_db = download_file_if_not_available(
        local_path=target_db_path,
        download_url=src_url,
    )

    conn = duckdb.connect(target_db)
    conn.create_function(
        "embed", embed, [duckdb.typing.VARCHAR], f"FLOAT[{get_embedding_size()}]"
    )

    q = {"q": query, "k": top_k}
    df = (
        conn.execute(
            """
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
            """,
            q,
        )
        .df()
        .to_json(orient="records")
    )
    conn.close()
    return df
