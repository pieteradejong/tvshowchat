"""The embedding model is pinned to an exact upstream commit."""
import re

from app.services import embedder


def test_model_revision_is_a_full_commit_sha():
    # A branch or tag name ("main", "v1") can be moved upstream; a sha cannot.
    assert re.fullmatch(r"[0-9a-f]{40}", embedder.EMBEDDING_MODEL_REVISION)


def test_no_unpinned_model_loads_in_app_code():
    from tests.conftest import ROOT

    offenders = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "app").rglob("*.py")
        if p.name != "embedder.py" and "SentenceTransformer(" in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"load the model via app.services.embedder: {offenders}"
