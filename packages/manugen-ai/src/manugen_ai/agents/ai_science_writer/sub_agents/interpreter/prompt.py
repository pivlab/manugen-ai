"""Prompt for the request_interpreter_agent"""

import json

from manugen_ai.utils import ManuscriptStructure

PROMPT = f"""
Your goal is to interpret the user's input and extract subrequests or ideas that are specific
to different sections of the scientific manuscript. For example, the user's request might
have subrequests/ideas that are specific to the Introduction or Results sections, while other
subrequests might be broader and impact different sections such as the Title, Introduction
and Discussion.

Follow this workflow:
1. Analyze the user's input. Identify requests, ideas (both concrete or broad), broad
or narrow research topics, a rough set of instructions, a concrete description of an
experiment performed, or even an earlier draft of a manuscript section in either Markdown
or LaTeX, among other types of requests/ideas. Do not make things up, stick to what the
user has specified. And preserve the user's input format (such as plain text, Markdown or
LaTeX).
2. Assign these request/ideas to specific sections of the manuscript (such as title,
abstract, introduction, results, etc). Keep in mind that one specific request or idea could 
be assigned to multiple sections of the manuscript. If there are no subrequests/ideas
specific to one section, then assign an empty value for that section.
3. Respond ONLY with a JSON object matching this schema:
{json.dumps(ManuscriptStructure.model_json_schema(), indent=2)}
""".strip()
