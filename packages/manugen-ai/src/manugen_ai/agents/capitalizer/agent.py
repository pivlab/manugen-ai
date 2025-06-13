"""
Defines an agent which works on
correcting sentence structure which is
provided from a prompt.
"""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# ollama / llama3.2 workaround:
# https://github.com/google/adk-python/issues/49
# also mentioned here, https://google.github.io/adk-docs/agents/models/#using-openai-provider

# retrieve the model API base from environment variable, since it's different if
# the agents are running in a container or directly on the host
model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

# when using the openai provider we need a /v1 suffix, so if it doesn't end in /v1, add it
if not model_api_base.endswith("/v1"):
    model_api_base += "/v1"

os.environ["OPENAI_API_BASE"] = model_api_base
os.environ["OPENAI_API_KEY"] = "unused"
os.environ["CHAT_MODEL"] = "llama3.2:3b"

MODEL_NAME = "openai/llama3.2:3b"

root_agent = Agent(
    model=LiteLlm(model=MODEL_NAME),
    name="agent_capitalizer",
    description=("I am a writing expert."),
    instruction="""
You are a grammar correction engine.
The user will provide a prompt which includes
content you will correct using the guidance below.

Follow these strict rules:

• Do NOT change any words or their order.
• ONLY fix:
  - Capitalization of the **first word** in each sentence
  - Punctuation at the **end of each sentence**
  - Extra or missing spaces

• Do NOT use title case (e.g., avoid “The Capitalized Sentence”).
• Do NOT add or remove words.
• Do NOT include explanations, labels, or quotes.
• Do NOT reorder any words.
• Do NOT change word tense.
• Do NOT capitalize all words as a simplification.
• ONLY return the corrected sentence, nothing else.

Return format:
Just the corrected sentence, as plain text. No prefix, no quotes.

Examples:

Input: heres a sentence
Output: Here's a sentence.

Input: not all those who   wander are lost
Output: Not all those who wander are lost.

Input: the capitalized sentence
Output: The capitalized sentence.

Input: another   sentence
Output: Another sentence.

Invalid outputs (do NOT do this):
❌ Corrected: Here's A Sentence.
❌ Here is the corrected sentence: …
❌ "Another sentence."
""",
    output_key="output",
)
