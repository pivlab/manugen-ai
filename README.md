# ADK Hackathon 2025

This repo holds our submission for the 2025 [Agent Development Kit Hackathon with Google Cloud](https://googlecloudmultiagents.devpost.com/).

The project consists of a web-based frontend, backend, and additional services.
It includes Docker Compose configuration to run the application stack locally.

The application stack relies on a package called *Manugen AI*, a multi-agent tool for creating academic manuscripts from a collection of images, text, and other content files.
See the [Manugen AI package README](packages/manugen-ai/README.md) for more details on the package itself.

## Prerequisites

### Ollama

To run models locally, you'll need to have [Ollama](https://ollama.com/) installed on your machine.
Once you have Ollama installed, you'll need to pull the Mistral Small 3.1 model, which is used by the *Manugen AI* package for invoking tools and generating text.

```bash
ollama pull mistral-small3.1
```

You'll then want to run the Ollama server, which will allow the application to access the model:

```bash
ollama serve
```

If you'd like to see if your Ollama server is accepting requests, you can run the following command on OS X to tail the server logs:

```bash
tail -f ~/.ollama/logs/server.log
```

## Installation

To run the full stack, you'll need Docker and Docker Compose installed on your machine.
See here for [installation instructions for Docker](https://docs.docker.com/get-docker/).

Docker Compose is typically included with Docker Desktop installations, but if you need to install it separately, see [the Docker Compose installation instructions](https://docs.docker.com/compose/install/).

To install the project, clone the repository and run:

```bash
docker compose up --build
```

This will build the Docker images and start the application.
You'll be attached to the logs of the application, which will show you live output from the various services that make up the stack.
Pressing `Ctrl+C` will stop the application.

Wait until you see the following message in the logs:

```
+-----------------------------------------------------------------------------+
| ADK Web Server started                                                      |
|                                                                             |
| For local testing, access at http://localhost:8000.                         |
+-----------------------------------------------------------------------------+
```

*(Note that the port within the container, 8000, is different than the one on the host, to prevent collisions.)*

Visit http://localhost:8900 in your web browser to access the ADK web agent interface.

## Usage

Once the application is running, you can access the web interface at `http://localhost:3000`.

### Command Line Interface

If you'd prefer not to use the web interface, you can also run the *Manugen AI* package from the command line.

You can use the package directly for this (see the package docs), but if you'd prefer to run it from within a Docker container, you can use the following command:

```bash
# first, build the image if you haven't already, or if you've made changes to the package
docker compose --profile cli build manugen

# then, execute it, replacing './content/' with the path to your content files
docker compose --profile cli run --build --rm \
    -v ./content/:/content/ \
    manugen
```

Currently the command runs the *Manugen AI* package's `cli` module with the `--content-dir` option set to `/content/`, which is the directory where the content files are mounted in the Docker container.
*TBC: add where the output files are saved, once that's implemented.*

## Other Resources

- *For project members: [internal planning doc](https://olucdenver.sharepoint.com/:w:/r/sites/CenterforHealthAI939-SoftwareEngineering/Shared%20Documents/Software%20Engineering/Projects/PivLab%20-%20ADK%20Hackathon/Agent%20Development%20Kit%20Hackathon%20with%20Google%20Cloud.docx?d=w0cfff935f2754c3492489ef5b15fe2f4&csf=1&web=1&e=NRM3en)*
