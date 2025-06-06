# Manugen AI

*Manugen AI* is a multi-agent tool for creating academic manuscripts from a collection of images, text, and other content files.
It leverages the capabilities of large language models (LLMs) to automate the generation of manuscripts, making it easier for researchers to produce first drafts of academic papers.

We intend to submit this project to the 2025 [Agent Development Kit Hackathon with Google Cloud](https://googlecloudmultiagents.devpost.com/).

## Installation

The project relies on [uv](https://docs.astral.sh/uv/) for dependency management.

To install the project, run:

```bash
uv venv # creates a virtual environment
source .venv/bin/activate # activates the virtual environment
uv sync # updates your new venv with the project's dependencies
```

## Usage

The project can be used both as a command line tool and as a Python package.

### Command Line Interface

To run the project from the command line, you can use the following command:

```bash
uv run manugen <content_dir>
```

Where `<content_dir>` is the path to the directory containing the content files.

### Python API

You can also use the project as a Python package. Here is an example of how to use it in your code:

```python
from pathlib import Path
from manugen_ai.cli import manugen

manugen(
    content_dir=Path("/path/to/content"),
    output_dir=Path("/path/to/output")
)
```

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for details on how to contribute to the project.

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE.md](LICENSE.md) file for details.

## Code of Conduct

Please read the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) file for details on our code of conduct and how we expect contributors to behave in the community.

## Acknowledgements

This project is primarily developed by DBMI's Software Engineering Team (SET) in collaboration with the Pividori Lab at the University of Colorado Anschutz Medical Campus.
We acknowledge the contributions of all community members and collaborators who have helped shape this project.
