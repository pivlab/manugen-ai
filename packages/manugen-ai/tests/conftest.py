"""
conftest for pytest fixutres and related
"""

import os
import pathlib
import tempfile
from typing import Any, Generator

import pytest


@pytest.fixture(autouse=True, scope="session")
def set_model_name_env():
    os.environ["MANUGENAI_MODEL_NAME"] = "openai/llama3.2:3b"
    os.environ["MANUGENAI_FIGURE_MODEL_NAME"] = "openai/llama3.2:3b"


@pytest.fixture
def temp_markdown_dir() -> Generator[
    pathlib.Path,
    Any,
    Any,
]:
    temp_dir = tempfile.TemporaryDirectory()
    dir_path = pathlib.Path(temp_dir.name)
    # Create example markdown files
    (dir_path / "README.md").write_text("# Example Project\n\nThis is a sample README.")
    (dir_path / "intro.md").write_text("# Introduction\n\nWelcome to the example.")
    (dir_path / "methods.md").write_text("# Methods\n\nDetails about the methods.")
    yield dir_path
    temp_dir.cleanup()
