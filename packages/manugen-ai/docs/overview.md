# Manugen AI - Agent Development Kit Hackathon with Google Cloud

![](media/manuscript_deadlines.png)

Researchers today navigate an increasingly complex landscape: from securing funding and navigating ethical approvals to designing robust methodologies and managing ever-growing datasets, the path from hypothesis to discovery is fraught with logistical, technical, and interpersonal hurdles.
Yet even once experiments conclude and results are compelling, a new challenge emerges—translating months, or sometimes years, of work into a concise, coherent, and publishable manuscript.
Crafting such a paper demands mastery not only of scientific rigor but also of narrative flow, clarity of argument, and precise language, all under the pressure of journal deadlines and peer review.
These dual demands often pull scientists in opposite directions: immersed in the nitty-gritty of data collection and analysis, they must then shift gears to adopt the wide-angle lens of storytelling, framing the big question, situating findings within a broader scholarly conversation, and articulating implications for future work.
Moreover, time spent polishing figures, formatting references, and resolving reviewer comments is time diverted from deeper scientific inquiry—yet without this effort, the impact of the research remains unrealized, making writing not a mere afterthought but an integral and often underestimated component of the scientific endeavor.

### A Real-World Test of Google-ADK

![](media/hackathon.png)

We saw the Devpost hackathon as an ideal proving ground for Google’s Agent Development Kit because it offered a fast-paced, collaborative setting in which to experiment with orchestrating specialized AI agents end-to-end.
In a short amount of time, we could spin up retrieval, summarization, drafting, and revision agents, wire them together through ADK’s built-in state management, and immediately observe how small prompt tweaks or workflow adjustments affected overall output quality.
The hackathon’s tight timeframe forced us to confront real-world integration and error-handling challenges—everything from passing context cleanly between agents to gracefully recovering from unexpected generation failures—while also giving us confidence that an agent-based architecture can dramatically streamline the scientific writing process.

## What Inspired Us

From the outset, we were captivated by the promise of autonomous AI agents collaborating to tackle complex, multidisciplinary tasks.
The Agent Development Kit Hackathon with Google Cloud challenged participants to “build autonomous multi-agent AI systems” capable of content creation, among other applications.

![](media/ai_assisted_writing.png)

Recognizing that writing a rigorous scientific manuscript involves navigating vast literature, synthesizing nuanced insights, and maintaining a coherent narrative, we saw an opportunity to apply multi-agent orchestration to streamline and elevate the research-writing process.
The hackathon’s emphasis on orchestrated agent interactions inspired us to ask: what if specialized agents—each expert in retrieval, summarization, drafting, and revision—could work in concert to produce a high-quality scientific paper?

## What We Learned

![](media/writing_assistance_workflow.png)

- **Modular Agent Design Is Essential.** By decomposing the writing process into discrete stages—literature retrieval, abstract summarization, section drafting, and peer-review simulation—we discovered that agents with narrowly scoped responsibilities could be more effectively tuned and evaluated.
  This division of labor not only improved output quality but also made debugging and iterating on individual components far more manageable.
- **Prompt Engineering Drives Quality.** Small changes in how we prompted each agent had outsized effects on coherence, style, and factual accuracy.
  Iteratively refining prompts based on error modes (e.g., hallucinations in data-driven sections, insufficient context in methods descriptions) emerged as a critical skill.
- **Integrating Retrieval Strengthens Rigor.** Leveraging a dedicated retrieval agent which queries [OpenAlex](https://openalex.org/) to ensured that our drafts were firmly grounded in existing literature, rather than relying solely on generative models.
  We also used [WithdrarXiv](https://arxiv.org/abs/2412.03775) through a custom-built vector embeddings database to help avoid reasons for retraction based on similar content.
  This hybrid retrieval-augmented approach helps reduce fabricated citations and avoids reasons for retraction to improve manuscripts scientific credibility.
- **Automated Feedback Is Powerful, but Imperfect.** Implementing a “peer-review” agent that applied heuristic and model-based checks (e.g., ensuring the presence of hypothesis statements, verifying statistical claims against source data) highlighted both the potential and current limitations of automated review.
  While it caught many structural issues, nuanced scientific arguments still required human oversight.

## How We Built Our Project

![](media/manugen-ai-frontend.png)

1. **User Interface.**
   We created a web interface which helps users write their paper content with the help of AI‐assistant actions.
   Under the hood, we used FastAPI to provide an API service layer to a Vue.js front‐end.
   This streamlined interface means that users can quickly get input on their work directly in a browser.
   It offers an intuitive writing environment that offers agentic input in the form of specific actions.
   Users can leverage one of many options which described in detail below.
   Once agents have taken actions on the content, users may analyze the results and make iterative improvements on the content.

![](media/coordinator_agent.png)

2. **Agent Roles & Pipeline:**

We used the Python version of ADK to define each agent’s behavior and orchestrate the workflow, tapping into its built-in support for asynchronous execution and state management.

- **Coordinator Agent:** An LlmAgent that orchestrates the entire manuscript workflow—initializing the prompt template, dispatching tasks to sub-agents (drafting, figures, citations, review, repo extraction), managing shared context and state, and collating each agent’s outputs into a unified draft.
- **Manuscript Drafter Agent:** An LlmAgent that takes the core prompt template and synthesizes full manuscript sections (Introduction, Methods, Results, Discussion), weaving together background, experimental details, and findings into a coherent draft.
- **Figure Agent:** Responsible for generating or formatting scientific figures—pulling in data, rendering plots or diagrams, and embedding them with appropriate captions so that visuals integrate seamlessly with the text.
- **Citation Agent:** Manages all bibliographic work by querying OpenAlex, verifying and formatting references, and inserting in‐text citations and a properly styled reference list.
- **Review Agent:** Acts as an automated peer reviewer—scanning each draft for logical flow, missing or incorrect citations, adherence to target journal guidelines, and surfacing any issues (e.g., potential retractions or style violations) back to the drafting agents.
- **Repository‐to‐Paper Agent:** Extracts methods and implementation details directly from your code repository—parsing README, docstrings, or example scripts—to generate the “Code & Methods” and Supplementary sections, ensuring the manuscript accurately reflects the underlying software.

## Challenges We Faced

- **Maintaining Coherence Across Agents.**
  As agents operated asynchronously, ensuring that context (e.g., variable definitions, methodological details) persisted seamlessly between stages required rigorous state-management strategies and periodic context re-injection.
- **Balancing Creativity and Accuracy.**
  Generative models can produce eloquent prose but may introduce factual inconsistencies. We mitigated this by tightly coupling drafting with retrieval, but tuning the trade-off between expressive writing and strict factuality was an ongoing challenge.
- **Scaling Retrieval Latency.**
  Querying large publication databases in real time sometimes introduced delays. Caching strategies and batched queries alleviated but did not eliminate occasional slowdowns under hackathon time constraints.
- **Human-in-the-Loop Necessity.**
  Despite our multi-agent setup, final quality assurance still relied on human review for nuanced interpretation, ethical considerations (e.g., avoiding unintended bias), and the final polish necessary for publication-ready prose.

## Conclusion and Future Directions

![](media/ai_and_scientist_bright_future.png)

Participating in the Devpost hackathon was an exhilarating journey that validated the power of multi-agent AI in scientific writing.
In a short amount of time, we witnessed firsthand how coordinated agents could accelerate literature review, draft coherent sections, generate figures, manage citations, and even perform automated “peer review.”
The collaborative hackathon environment pushed us to solve real-world integration challenges under tight deadlines, and the results exceeded our expectations—our prototype delivered draft manuscripts far more quickly than traditional workflows.

Looking ahead, we’re excited to iterate on this foundation: refining prompt strategies to further reduce factual errors, experimenting with additional sub-agents (e.g., for data analysis or ethical bias checks), and exploring integrations with more diverse data sources.
By continuously benchmarking against human-authored papers and expanding our agent toolkit, we aim to uncover the full potential of Google-ADK for research writing.
This hackathon was just the beginning, and we’re eager to push the boundaries of what autonomous AI collaborations can achieve in scholarly publishing.
