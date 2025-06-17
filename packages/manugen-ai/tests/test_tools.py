import pathlib
from types import SimpleNamespace

import pygit2
import pytest
from manugen_ai.tools.tools import (
    clone_repository,
    exit_loop,
    fetch_url,
    json_conforms_to_schema,
    parse_list,
    read_path_contents,
    semantic_scholar_search,
)


def test_parse_list_basic() -> None:
    """Ensure parse_list splits text into clean list items."""
    text: str = """
    - first item
    * second item
    third item

    """
    assert parse_list(text) == ["first item", "second item", "third item"]


def test_semantic_scholar_search_empty() -> None:
    """Verify that an empty topics list returns an empty dict without API calls."""
    topics: list[str] = []
    assert semantic_scholar_search(topics) == {}


def test_semantic_scholar_search_real() -> None:
    """Check semantic_scholar_search returns dict of URLs for a real query."""
    topics: list[str] = ["neural networks"]
    result: dict[str, list[str]] = semantic_scholar_search(topics, limit=1)
    assert isinstance(result, dict)
    assert "neural networks" in result
    urls: list[str] = result["neural networks"]
    assert isinstance(urls, list)
    assert len(urls) <= 1
    for url in urls:
        assert url.startswith("http")


def test_fetch_url_real() -> None:
    """Fetch example.com and confirm known content is present."""
    text: str = fetch_url("http://example.com")
    assert "Example Domain" in text


def test_exit_loop_sets_escalate() -> None:
    """Ensure exit_loop sets the escalate flag on the ToolContext."""
    fake_ctx: SimpleNamespace = SimpleNamespace(
        agent_name="my_agent", actions=SimpleNamespace(escalate=False)
    )
    ret: dict = exit_loop(fake_ctx)
    assert ret == {}
    assert fake_ctx.actions.escalate is True


def test_json_conforms_to_schema_valid() -> None:
    """Validate JSON string against a matching schema returns True."""
    raw: str = '{"a": 1, "b": "foo"}'
    schema: dict = {
        "type": "object",
        "properties": {"a": {"type": "number"}, "b": {"type": "string"}},
        "required": ["a", "b"],
    }
    assert json_conforms_to_schema(raw, schema) is True


def test_json_conforms_to_schema_invalid_json() -> None:
    """Invalid JSON input should return False."""
    bad_raw: str = "not json"
    assert json_conforms_to_schema(bad_raw, {}) is False


def test_json_conforms_to_schema_invalid_schema() -> None:
    """JSON that doesn't match the schema returns False."""
    raw: str = '{"a": "oops"}'
    schema: dict = {"type": "object", "properties": {"a": {"type": "number"}}}
    assert json_conforms_to_schema(raw, schema) is False


def test_read_path_contents_file(tmp_path: pathlib.Path) -> None:
    """Read contents of a single file and trim whitespace."""
    f: pathlib.Path = tmp_path / "hello.txt"
    f.write_text("  Hello world  ")
    out: str = read_path_contents(str(f))
    assert out == "Hello world"


def test_read_path_contents_dir(tmp_path: pathlib.Path) -> None:
    """Read text from all files in a directory and combine."""
    d: pathlib.Path = tmp_path / "sub"
    d.mkdir()
    (d / "a.md").write_text("foo")
    (d / "b.py").write_text("bar")
    combined: str = read_path_contents(str(tmp_path))
    assert "foo" in combined
    assert "bar" in combined


def test_read_path_contents_not_found(tmp_path: pathlib.Path) -> None:
    """Requesting a non-existent path should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_path_contents(str(tmp_path / "does_not_exist"))


def test_clone_repository_local(tmp_path: pathlib.Path) -> None:
    """Clone a locally initialized bare repo and verify .git directory exists."""
    origin: pathlib.Path = tmp_path / "origin.git"
    pygit2.init_repository(str(origin), bare=True)
    repo_path: str = clone_repository(str(origin))
    repo_dir: pathlib.Path = pathlib.Path(repo_path)
    assert repo_dir.exists()
    assert (repo_dir / ".git").exists()
