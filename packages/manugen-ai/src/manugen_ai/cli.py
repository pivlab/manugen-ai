import os
from pathlib import Path
from cyclopts import App

from dotenv import load_dotenv

# load up secrets from a .env file in the first ancestor directory that contains
# one (typically the root of the project)
load_dotenv()

app = App()


@app.default
def manugen(content_dir: Path, output_dir: Path = None):
    """
    Manugen AI CLI - A command line interface for Manugen AI.

    Ingests content from the content directory and processes it, saving the output
    to the specified output directory or a default subdirectory of the content directory.

    Args:
        content_dir (Path): The directory containing the content to process.
        output_dir (Path, optional): The directory where the output will be saved.
            If not specified, defaults to a subdirectory named '_output' within the content directory.
    """
    print("* Manugen AI CLI *")
    print(f"- Ollama API URL: {os.environ.get('OLLAMA_API_BASE', '<not set>')}")
    print(f"- Input content directory: {content_dir.resolve()}")

    if output_dir:
        print(f"- Output directory: {output_dir.resolve()}")
    else:
        output_dir = content_dir / "_output"
        print(f"- No output directory specified, using default of {output_dir}.")

    print()
    print("**Implementation TBC**")
    print()


if __name__ == "__main__":
    app()
