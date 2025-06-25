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

## Get started

- 🎥 Watch our demo [YouTube video](https://youtu.be/WkfA-7lXE5w?si=7P_1BMonfFpm_2YE)
- 🔖 Read our [blog post](https://pivlab.org/2025/06/23/Google-ADK-Hackathon.html)

## Project Structure

The project is a standard three-tier web application, with the following components:

- `./frontend/`: A web-based user interface for interacting with the application, built with React.
- `./backend/`: A REST API that serves the frontend and handles requests from the web interface.
- `./packages/manugen-ai/`: The *Manugen AI* package, which is used to generate academic manuscripts from content files.
  The backend relies on this package to perform the actual manuscript generation.

The project includes an optional PostgreSQL database that, if available, ADK will use to persist session data between stack runs.

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
To check the logs in OS X, you can run the following command to tail the server logs: `tail -f ~/.ollama/logs/server.log`.

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
In general, larger models perform better (you can try larger versions of Qwen3 and Gemma3), provided you have a GPU with sufficient VRAM to maintain acceptable inference times.


## Usage

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

**Third**, run the project:

```bash
docker compose up --build
```

This will build the Docker images and start the application.
You'll be attached to the logs of the application, which will show you live output from the various services that make up the stack.
Pressing `Ctrl+C` will stop the application.

Wait until you see a message resembling the following in the logs:

### Accessing the Frontend

```
VITE v6.3.5  ready in 1276 ms

➜  Local:   http://localhost:5173/
➜  Network: http://172.22.0.2:5173/
```

Browse to http://localhost:8901 and you should see the frontend.
It might take a few seconds to establish a connection.

*(FYI: Despite the port being 5173 in the logs, the Docker Compose configuration maps it to port 8901 on the host machine.)*

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

## Other Resources

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
