# Manugen AI

<img align="left" src="packages/manugen-ai/docs/media/manugen-ai-logo.png" alt="Project Logo" width="300px" />

Writing academic manuscripts can be tedious.
Imagine that you could bring together your results, prior research, source code, and some brief bullet points per section to generate a manuscript automatically.
That is **Manugen-AI**.

This repo holds our submission for the 2025 [Agent Development Kit (ADK) Hackathon with Google Cloud](https://googlecloudmultiagents.devpost.com/) - Manugen AI.
**Manugen AI** is a multi-agent tool for drafting academic manuscripts from assets and guidance: a collection of figures, text/instructions, source code, and other content files.
It uses agents based on large language models (LLMs) and the [Google ADK](https://google.github.io/adk-docs/).
See the [Manugen AI package README](packages/manugen-ai/README.md) for more details on the package itself.

The project consists of a web-based frontend, backend, and additional services.
It includes Docker Compose configuration to run the application stack locally.

<div style="clear: both;">&nbsp;</div>

**🚧 NOTE**:
This product was initially made as part of a hackathon under very tight time and resource limitations, which resulted in a rapidly improvised architecture and user interface.
Our experienced team of engineers intends to turn this proof-of-concept into a fully-fledged, robust system through ongoing funded work.

## Get started

- 🎥 Watch our demo [YouTube video](https://youtu.be/WkfA-7lXE5w?si=7P_1BMonfFpm_2YE)
- 🔖 Read our [story on
  Medium](https://medium.com/@miltondp/manugen-ai-automatic-scientific-article-drafting-from-assets-and-guidance-47198ab0f244)

## Installation

### Docker and Docker Compose

To run the full stack, you'll need Docker and Docker Compose installed on your machine.
See here for [installation instructions for Docker](https://docs.docker.com/get-docker/).

Docker Compose is typically included with Docker Desktop installations, but if you need to install it separately, see [the Docker Compose installation instructions](https://docs.docker.com/compose/install/).

### (Optional) Ollama for local LLM models

If you want to run LLM models locally, you'll need to have [Ollama](https://ollama.com/) installed on your machine.
Once you have Ollama installed, you want to run the Ollama server, which will allow the application to access the model.
Make sure the Ollama server is listening to all addresses so you can use our Docker images.
If the Ollama server is running as a system service already, stop it first (in Ubuntu Linux, you'll need to run `sudo systemctl stop ollama.service`).
Then, start it manually:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

Make sure the Ollama server is accepting requests by inspecting the logs.
The command above should output something like `"Listening on [::]:11434"` (it *should not* include `127.0.0.1`, otherwise we won't be able to connect to it from a Docker container).
To check the logs in macOS, you can run the following command to tail the server logs: `tail -f ~/.ollama/logs/server.log`.

Then, you'll need to pull a model of your choice, which is used by the *Manugen AI* package for invoking tools, generating text, and interpreting figures.
Make sure the model you pick [supports "tools"](https://ollama.com/search?c=tools), such as [Qwen3](https://ollama.com/library/qwen3):

```bash
# qwen3 supports tools and thinking
ollama pull qwen3:8b
```

If you want to use Manugen-AI to upload figures and interpret them, you'll also need a model that [supports "vision"](https://ollama.com/search?c=vision), such as [Gemma3](https://ollama.com/library/gemma3):

```bash
# gemma3 supports vision, which can be used to interpret your figures
ollama pull gemma3:4b
```

For the sake of keeping computational demands low, **the models suggested here are small and may not yield the best results.**
You'll need to test which model works best for your task.
In general, we've observed that large models or those with high context size perform better (you can try larger versions of Qwen3 and Gemma3), provided you have a GPU with sufficient VRAM to maintain acceptable inference times.

### Adjut settings (API keys, etc)

**First**, clone the repository, and in a terminal, change directory to the repo folder.

**Second**, copy `.env.TEMPLATE` in the root of the project to a file named `.env`:

```bash
cp .env.TEMPLATE .env
```

Then take a look at the `.env` file for other options.
You'll also want to fill out API keys for services you're using.
Currently, the project uses Google's Gemini 2.5 model (`gemini-2.5-flash`), so if you want to use it as well, you'll need a valid API key value for the `GOOGLE_API_KEY` entry.

If you want to use an Ollama model, make sure you select it by changing the value of `MANUGENAI_MODEL_NAME` (and maybe `MANUGENAI_FIGURE_MODEL_NAME`) in the `.env` file:

```env
# if you want to use Ollama, select a model that supports "tools" such as Qwen3:
MANUGENAI_MODEL_NAME="ollama/qwen3:8b"

# Qwen3, however, does not support "vision" to interpret your figures
# So you can select a model that supports "vision" such as Gemma3:
MANUGENAI_FIGURE_MODEL_NAME="ollama/gemma3:4b"
```

## Usage

### Start the backend

Run the following command:

```bash
docker compose up --build
```

This will build the Docker images and start the application.
You'll be attached to the logs of the application, which will show you live output from the various services that make up the stack.
You can press `Ctrl+C` if you want to stop the application.

Wait until you see a message resembling the following in the logs:

```
VITE v6.3.5  ready in 1276 ms

➜  Local:   http://localhost:5173/
➜  Network: http://172.22.0.2:5173/
```

### Access the frontend

Use a web browser to open http://localhost:8901 and to view the frontend user interface.
It might take a few seconds to establish a connection.

*(FYI: Despite the port being 5173 in the logs, the Docker Compose configuration maps it to port 8901 on the host machine.)*

### Draft a manuscript

*(Remember this is a prototype system and it is still work-in-progress, so you might find bugs)*

Once you accessed the frontend in your browser, you can load the included example to draft a manuscript from scratch:

1. **Load an example of human guidelines:** click on the lightbulb icon ("Try an example") on the top right to load an example.
   This example represents some ideas that a human author might quickly sketch when thinking in a future scientific manuscript.
   These ideas might be a set of bullet points per section with early notes on how you are thinking about the structure, content, etc.
   We call this the "human guidelines" for Manugen-AI.
   The example corresponds to the guidelines for [this peer-reviewed article](https://doi.org/10.1016/j.cels.2024.08.005).
   You'll see the example is written in Markdown, with some ideas for the different sections (abstract, results, etc).
   This is what the most early version of your manuscript might look like, and will surely evolve with time.
1. **Draft a section:** to *draft* sections of the manuscript, you need to select the _entire section_ content and then click on the "Draft" action (see animation below).
   You can try with the entire Results section (which includes two subsections).
   When ready, the text you selected will be replaced by the draft.
1. **Edit an existing draft:** if you are not happy with the current draft, you can *edit* it by adding comments/instructions in the middle (such as bullet points before a paragraph or notes in the middle of the text with instructions for Manugen-AI), selecting the entire section, and clicking on "Draft" again.
1. **Upload figures:** you can upload figures by clicking on the paperclip icon on the top right corner.
   Once you upload a figure, Manugen-AI will interpret it by generating a title and a description that will be added to the internal state of the system, and used by the Results Agent when drafting this section.
   When you drafted the Results section in the steps above (which had references to "Figure 1", "Figure 2" and "Figure 3"), the system didn't have any figures added yet, so the agent did its best with the content you provided in the bullet points.
   Now, try to upload [Figures 1, 2 and 3 from this folder](frontend/public/example), and then *edit* the Results section (just select its text and click on the "Draft" action), and you'll see how its text now correctly references the actual content of the figures.

<img src="https://miro.medium.com/v2/resize:fit:720/format:webp/1*GXmqk39rXlR9bbiLP5FIsw.gif" alt="Project Logo" width="100%" />

### Create a manuscript based on a version controlled repository

Does your research involve the use of a version controlled repository (for example, hosted on GitHub)?
You can use Manugen AI to create a manuscript by passing the URL for the project with the "Repos" action.

1. Within the frontend, paste in a GitHub URL (e.g. `https://github.com/pivlab/manugen-ai`).
2. Highlight the GitHub URL and click the "Repos" action.
3. Manugen AI agents will absorb information about your repository and provide a draft manuscript in return.

### Enrich manuscript content with related citations

No manuscript is complete without citations from related work.
Enrich your content by using Manugen AI agents which query [OpenAlex](https://openalex.org/) through the "Cites" action.

1. Highlight any content within a draft manuscript in our front-end and click the "Cites" action.
2. Manugen AI will summarize the content and leverage OpenAlex to query for related citations.
3. Content is updated to include information with related citation.

### Avoid reasons for retraction

Maintaining the integrity and trustworthiness of the scientific record is paramount, and proactively avoiding retractions is a core responsibility.
Avoid reasons for retraction within manuscript content by using the "Retracts" action.

1. Highlight any content within a draft manuscript in our front-end and click the "Retracts" action.
2. Manugen AI will use retrieval-augmented generation (RAG) to find related reasons for retraction based on [WithdrarXiv](https://huggingface.co/datasets/darpa-scify/withdrarxiv).
3. Content is updated to avoid reasons for retraction based on this data.

## Other Resources

### Project Structure

The project is a standard three-tier web application, with the following components:

- `./frontend/`: A web-based user interface for interacting with the application, built with React.
- `./backend/`: A REST API that serves the frontend and handles requests from the web interface.
- `./packages/manugen-ai/`: The *Manugen AI* package, which is used to generate academic manuscripts from content files.
  The backend relies on this package to perform the actual manuscript generation.

The project includes an optional PostgreSQL database that, if available, ADK will use to persist session data between stack runs.

### Accessing the Backend API

While it's not necessary to use the app, you might want to access the backend API directly for testing or debugging purposes.

Wait until you see the following message in the logs:

```
INFO:     Will watch for changes in these directories: ['/app']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [102] using WatchFiles
INFO:     Started server process [104]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Visit http://localhost:8900 in your web browser to access the backend API; docs can be found at http://localhost:8900/docs.

*(Again, note that the port within the container, 8000, is different than the one on the host to prevent collisions with other host services.)*

### Purging Session State

If you want to clear the session state, you can run the following command to stop any application containers that are running and remove the database volume:

```bash
docker compose down -v
```

This will purge any sessions or other data that ADK stores to the database.

### (Optional) Running the App in Production

The app includes configuration, located in `docker-compose.prod.yml`, for running the application in production mode.

To use it, ensure that you've updated `DOMAIN_NAME` in your `.env` file to the domain name under which the app will be served.
You should also ensure that you have access to map ports 80 and 443 on the machine that will be running the production app.

The production configuration differs from the development configuration in a few ways:

- The frontend is built and served as static files, rather than being served by a development server.
- Volumes are disabled, and the code for each container is baked into the image. As a result, hot-reloading is disabled for all containers.
- It uses [Caddy](https://caddyserver.com/) as a reverse proxy to serve the frontend and backend as well as to obtain an SSL cert for your chosen domain.
  - The backend API is served from `/api/`
  - The frontend is served from `/`

To launch the production version of the app, you can run the following command:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

This will build the production images and start the application in detached mode.

To tail the container logs, you can run:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

- *For project members: [internal planning doc](https://olucdenver.sharepoint.com/:w:/r/sites/CenterforHealthAI939-SoftwareEngineering/Shared%20Documents/Software%20Engineering/Projects/PivLab%20-%20ADK%20Hackathon/Agent%20Development%20Kit%20Hackathon%20with%20Google%20Cloud.docx?d=w0cfff935f2754c3492489ef5b15fe2f4&csf=1&web=1&e=NRM3en)*

### (Optional) Running ADK Web

If you'd like to run the ADK web agent interface, you can do so by running the following command:

```bash
docker compose run -p 8905:8000 --rm -it backend /app/start_adk_web.sh
```

Wait until you see the following message in the logs:

```
+----------------------------------------------------------+
| ADK Web Server started                                   |
|                                                          |
| For local testing, access at http://localhost:8000.      |
+----------------------------------------------------------+
```

Visit http://localhost:8905 in your web browser to access the ADK web agent interface.
