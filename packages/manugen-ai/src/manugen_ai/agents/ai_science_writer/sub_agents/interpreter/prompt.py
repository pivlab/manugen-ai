"""Prompt for the request_interpreter_agent"""

import json

from manugen_ai.schema import ManuscriptStructure

PROMPT = f"""
Your goal is to interpret the user's input below and extract instructions, requests or ideas that are specific
to different sections of the scientific manuscript. For example, the user's input might
have instructions/requests/ideas that are specific to the Introduction or Results sections.

Follow this workflow:

1. Analyze the user's input. It can be plain text, Markdown or LaTex. Identify 
instructions, requests, ideas (both concrete or broad), broad or narrow research 
topics, a rough set of instructions, a concrete description of an experiment 
performed, or even an earlier draft of a manuscript section in either Markdown or 
LaTeX, among other types of requests/ideas. Do not make things up, stick to what the 
user has specified. And preserve the user's input format (such as plain text, 
Markdown or LaTeX).
2. Assign these request/ideas to specific sections of the manuscript (such as title, 
abstract, introduction, results, etc). Usually, you will identify the section of the 
manuscript by looking at the top title of the user input (for example "# 
Introduction", "# Results", etc). Keep in mind that instructions/requests/ideas can 
only belong to one specific section, not to multiple ones. If there are no 
subrequests/ideas specific to one section, then assign an empty value for that section.
3. Respond ONLY with a JSON object matching this schema:
{json.dumps(ManuscriptStructure.model_json_schema(), indent=2)}

# User input
{{last_user_input}}
""".strip()
