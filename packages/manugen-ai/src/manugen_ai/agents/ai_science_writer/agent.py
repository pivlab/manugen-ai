import os
import json
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import Optional

model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

# when using the openai provider we need a /v1 suffix, so if it doesn't end in /v1, add it
if not model_api_base.endswith("/v1"):
    model_api_base += "/v1"

os.environ["OPENAI_API_BASE"] = model_api_base
os.environ["OPENAI_API_KEY"] = "unused"

MODEL_NAME = "openai/qwen3:30b"

# ccc_agent = Agent(
#     name="ccc_agent",
#     model=LiteLlm(model=MODEL_NAME),
#     description="Handles requests to check whether input text follows the context-content-conclusion (C-C-C) scheme."
# )

from pydantic import BaseModel, Field

class ManuscriptStructure(BaseModel):
    title: str = Field(description="Title.")
    keywords: str = Field(description="Keywords.")
    abstract: str = Field(description="Abstract.")
    introduction: str = Field(description="Introduction.")
    results: str = Field(description="Results.")
    # figures: dict[str, str] = Field(description="Figures IDs (keys) and any metadata (value).")
    # tables: dict[str, str] = Field(description="Tables IDs (keys) and any metadata (value).")
    # source_code_files: dict[str, str] = Field(description="Source code file IDs (keys) and any metadata (value).")
    discussion: str = Field(description="Discussion.")
    methods: str = Field(description="Methods.")

article_structure_agent = Agent(
    name="article_structure_agent",
    model=LiteLlm(model=MODEL_NAME),
    description="Extracts sections of the user input.",
    instruction=f"""
    Given the input content of a scientific article in Markdown or LaTeX format, extract all the typical sections present
    in a scientific article (like the title, abstract, introduction, etc), including all their content in the original
    format (Markdown or LaTeX), and also individual components such as figures, tables, and source code files.
    Respond ONLY with a JSON object matching this exact schema:
    {json.dumps(ManuscriptStructure.model_json_schema(), indent=2)}
    """.strip(),
    output_schema=ManuscriptStructure,
    output_key="instructions"
)

def prepare_inputs(callback_context: CallbackContext) -> Optional[types.Content]:
    current_state = callback_context.state.to_dict()
    
    if "content" in current_state and "results" in current_state["content"]:
        callback_context.state["results"] = current_state["content"]["results"]
    else:
        callback_context.state["results"] = current_state["instructions"]["results"]
    
    if "content" in current_state and "introduction" in current_state["content"]:
        callback_context.state["introduction"] = current_state["content"]["introduction"]
    else:
        callback_context.state["introduction"] = current_state["instructions"]["introduction"]
        
    return None

results_agent = Agent(
    name="results_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting a Results section of a scientific manuscript given some rough instructions.",
    instruction="""
    You are an expert in drafting the Results section of a scientific manuscript.
    Your goal is to draft the Results section as a sequence of statements, supported by figures (if present),
    that connect logically to support the central contribution. The results section needs to convince the
    reader that the central claim is supported by data and logic.
    Given the rough set of instructions and/or ideas for a Results section below, you will:
    1. Group the instructions/ideas into a set of declarative statements that will become the headers of subsections within
    the Results section.
    2. For each of these subsections, you will follow the guidelines below to convert the rough set
    of instructions/ideas, into a set of properly structured paragraphs. 
    
    **Rough instructions and/or ideas for the Results section**:
    ```
    {results}
    ```
    
    **Current Introduction content or rough instructions and/or ideas for the Introduction section**:
    ```
    {introduction}
    ```
    
    **Guidelines for the Results section**:
    ```
    * The first results paragraph is special in that it typically summarizes the 
    overall approach to the problem outlined in the introduction, along with any key 
    innovative methods that were developed. Most readers do not read the methods, 
    so this paragraph gives them the gist of the methods that were used.
    
    * Each subsequent paragraph in the results section starts with a sentence or two 
    that set up the question that the paragraph answers, such as the following: “To 
    verify that there are no artifacts…,” “What is the test-retest reliability of our 
    measure?,” or “We next tested whether Ca2+ flux through L-type Ca2+ channels was 
    involved.” The middle of the paragraph presents data and logic that pertain to 
    the question, and the paragraph ends with a sentence that answers the question. 
    For example, it may conclude that none of the potential artifacts were detected. 
    This structure makes it easy for experienced readers to fact-check a paper. Each 
    paragraph convinces the reader of the answer given in its last sentence. This 
    makes it easy to find the paragraph in which a suspicious conclusion is drawn and 
    to check the logic of that paragraph. The result of each paragraph is a logical 
    statement, and paragraphs farther down in the text rely on the logical 
    conclusions of previous paragraphs, much as theorems are built in mathematical 
    literature.
    ```
    
    **Output:**
    Output only the content of the Results section. Do not provide any explanation.
    """.strip(),
    before_agent_callback=prepare_inputs,
    output_key="results",
)

introduction_agent = Agent(
    name="introduction_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting an Introduction section of a scientific manuscript given some rough instructions.",
    instruction="""
    You are an expert in drafting the Introduction section of a scientific manuscript.
    Your goal is to draft the Introduction section that communicates why the scientific manuscript matters.
    For this, you will take the rough set of instructions and/or ideas for the Introduction section,
    and follow the guidelines for the Introduction below to draft it, while connecting it with the current Results section
    for context.

    **Rough instructions and/or ideas for the Introduction section**:
    ```
    {introduction}
    ```

    **Current Results section**:
    ```
    {results}
    ```

    **Guidelines for the Results section**:
    ```
    * The introduction highlights the gap that exists in current knowledge or methods 
    and why it is important. This is usually done by a set of progressively more 
    specific paragraphs that culminate in a clear exposition of what is lacking in 
    the literature, followed by a paragraph summarizing what the paper does to fill 
    that gap.
    
    * As an example of the progression of gaps, a first paragraph may explain why 
    understanding cell differentiation is an important topic and that the field has 
    not yet solved what triggers it (a field gap). A second paragraph may explain 
    what is unknown about the differentiation of a specific cell type, such as 
    astrocytes (a subfield gap). A third may provide clues that a particular gene 
    might drive astrocytic differentiation and then state that this hypothesis is 
    untested (the gap within the subfield that you will fill). The gap statement sets 
    the reader’s expectation for what the paper will deliver.
    
    * The structure of each introduction paragraph (except the last) serves the goal 
    of developing the gap. Each paragraph first orients the reader to the topic (a 
    context sentence or two) and then explains the "knowns" in the relevant 
    literature (content) before landing on the critical “unknown” (conclusion) that 
    makes the paper matter at the relevant scale. Along the path, there are often 
    clues given about the mystery behind the gaps; these clues lead to the untested 
    hypothesis or undeveloped method of the paper and give the reader hope that the 
    mystery is solvable. The introduction should not contain a broad literature 
    review beyond the motivation of the paper. This gap-focused structure makes it 
    easy for experienced readers to evaluate the potential importance of a paper—they 
    only need to assess the importance of the claimed gap.
    
    * The last paragraph of the introduction is special: it compactly summarizes the 
    results, which fill the gap you just established. It differs from the abstract in 
    the following ways: it does not need to present the context (which has just been 
    given), it is somewhat more specific about the results, and it only briefly 
    previews the conclusion of the paper, if at all.
    ```

    **Output:**
    Output only the content of the Introduction section. Do not provide any explanation.
    """.strip(),
    before_agent_callback=prepare_inputs,
    output_key="introduction",
)

root_agent = SequentialAgent(
    name="scientific_article_writer",
    description="Writes a scientific article",
    sub_agents=[
        article_structure_agent,
        results_agent,
        introduction_agent,
    ],
)
