# HuggingFace Model Cache

This directory is used to store cached models from HuggingFace.

If `USE_GEMINI_EMBEDDINGS` is not 1, [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding)
will be used instead, and the embeddings will be downloaded when the API server boots and stored in this folder.

Otherwise, Gemini embeddings will be used via the Google GenAI API, in which case this folder will be empty.
