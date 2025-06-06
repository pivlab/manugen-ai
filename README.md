# ADK Hackathon 2025

This repo holds our submission for the 2025 [Agent Development Kit Hackathon with Google Cloud](https://googlecloudmultiagents.devpost.com/).

The project consists of a web-based frontend, backend, and additional services.
It includes Docker Compose configuration to run the application stack locally.

The application stack relies on a package called *Manugen AI*, a multi-agent tool for creating academic manuscripts from a collection of images, text, and other content files.
See the [Manugen AI package README](packages/manugen-ai/README.md) for more details on the package itself.

## Installation

To run the full stack, you'll need Docker and Docker Compose installed on your machine.
See here for [installation instructions for Docker](https://docs.docker.com/get-docker/).

Docker Compose is typically included with Docker Desktop installations, but if you need to install it separately, see [the Docker Compose installation instructions](https://docs.docker.com/compose/install/).

To install the project, clone the repository and run:

```bash
docker compose up --build
```

This will build the Docker images and start the application.


## Usage

Once the application is running, you can access the web interface at `http://localhost:3000`.

### Command Line Interface

If you'd prefer not to use the web interface, you can also run the *Manugen AI* package from the command line.

You can use the package directly for this (see the package docs), but if you'd prefer to run it from within a Docker container, you can use the following command:

```bash
docker compose run manugen -v <content_dir>:/content manugen /content
```

Where `<content_dir>` is the path to the directory containing the content files.


## Other Resources

- *For project members: [internal planning doc](https://olucdenver.sharepoint.com/:w:/r/sites/CenterforHealthAI939-SoftwareEngineering/Shared%20Documents/Software%20Engineering/Projects/PivLab%20-%20ADK%20Hackathon/Agent%20Development%20Kit%20Hackathon%20with%20Google%20Cloud.docx?d=w0cfff935f2754c3492489ef5b15fe2f4&csf=1&web=1&e=NRM3en)*
