import json
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _install_groq_stub() -> None:
    try:
        import groq  # noqa: F401
        return
    except Exception:
        pass

    groq_module = types.ModuleType("groq")

    class _FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="stub response"))]
            )

    class _FakeChat:
        def __init__(self):
            self.completions = _FakeCompletions()

    class Groq:
        def __init__(self, *args, **kwargs):
            self.chat = _FakeChat()

    groq_module.Groq = Groq
    sys.modules["groq"] = groq_module


def _install_langchain_stubs() -> None:
    try:
        import langchain_groq  # noqa: F401
        import langchain_core.messages  # noqa: F401
        import langchain_core.output_parsers  # noqa: F401
        return
    except Exception:
        pass

    langchain_groq = types.ModuleType("langchain_groq")

    class ChatGroq:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, messages):
            return SimpleNamespace(content="{}")

    langchain_groq.ChatGroq = ChatGroq
    sys.modules["langchain_groq"] = langchain_groq

    langchain_core = types.ModuleType("langchain_core")
    messages_module = types.ModuleType("langchain_core.messages")
    output_parsers_module = types.ModuleType("langchain_core.output_parsers")

    class _Message:
        def __init__(self, content=""):
            self.content = content

    class SystemMessage(_Message):
        pass

    class HumanMessage(_Message):
        pass

    class AIMessage(_Message):
        pass

    class PydanticOutputParser:
        def __init__(self, pydantic_object):
            self.pydantic_object = pydantic_object

        def get_format_instructions(self):
            return "Return valid JSON."

        def parse(self, text):
            try:
                return self.pydantic_object.model_validate_json(text)
            except Exception:
                return self.pydantic_object.model_validate(
                    {
                        "profile": {},
                        "missing_fields": [],
                        "is_complete": False,
                        "next_question": None,
                    }
                )

    messages_module.SystemMessage = SystemMessage
    messages_module.HumanMessage = HumanMessage
    messages_module.AIMessage = AIMessage
    output_parsers_module.PydanticOutputParser = PydanticOutputParser

    sys.modules["langchain_core"] = langchain_core
    sys.modules["langchain_core.messages"] = messages_module
    sys.modules["langchain_core.output_parsers"] = output_parsers_module


def _install_sentence_transformer_stub() -> None:
    try:
        import sentence_transformers  # noqa: F401
        return
    except Exception:
        pass

    import numpy as np

    sentence_transformers = types.ModuleType("sentence_transformers")

    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True):
            vectors = np.array(
                [[float(len(t) % 7 + 1), 1.0, 0.5] for t in texts], dtype=float
            )
            if normalize_embeddings:
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                vectors = vectors / norms
            if convert_to_numpy:
                return vectors
            return vectors.tolist()

    sentence_transformers.SentenceTransformer = SentenceTransformer
    sys.modules["sentence_transformers"] = sentence_transformers


def _install_faiss_stub() -> None:
    try:
        import faiss  # noqa: F401
        return
    except Exception:
        pass

    import numpy as np

    faiss_module = types.ModuleType("faiss")

    class IndexFlatIP:
        def __init__(self, dim):
            self.dim = dim
            self.vectors = np.empty((0, dim), dtype="float32")

        def add(self, vectors):
            self.vectors = np.vstack([self.vectors, vectors])

        def search(self, query, top_k):
            if self.vectors.size == 0:
                return np.array([[]], dtype="float32"), np.array([[]], dtype=int)
            scores = np.dot(self.vectors, query[0])
            idx = np.argsort(-scores)[:top_k]
            return np.array([scores[idx]], dtype="float32"), np.array([idx], dtype=int)

    faiss_module.IndexFlatIP = IndexFlatIP
    sys.modules["faiss"] = faiss_module


def _install_bm25_stub() -> None:
    try:
        import rank_bm25  # noqa: F401
        return
    except Exception:
        pass

    bm25_module = types.ModuleType("rank_bm25")

    class BM25Okapi:
        def __init__(self, documents):
            self.documents = documents

        def get_scores(self, tokens):
            token_set = set(tokens)
            return [
                float(sum(1 for token in doc if token in token_set))
                for doc in self.documents
            ]

    bm25_module.BM25Okapi = BM25Okapi
    sys.modules["rank_bm25"] = bm25_module


def _install_google_and_youtube_stubs() -> None:
    try:
        import googleapiclient.discovery  # noqa: F401
    except Exception:
        googleapiclient = types.ModuleType("googleapiclient")
        discovery_module = types.ModuleType("googleapiclient.discovery")

        class _FakeSearchRequest:
            def execute(self):
                return {"items": []}

        class _FakeSearch:
            def list(self, **kwargs):
                return _FakeSearchRequest()

        class _FakeYouTube:
            def search(self):
                return _FakeSearch()

        def build(*args, **kwargs):
            return _FakeYouTube()

        discovery_module.build = build
        sys.modules["googleapiclient"] = googleapiclient
        sys.modules["googleapiclient.discovery"] = discovery_module

    try:
        import youtube_transcript_api  # noqa: F401
    except Exception:
        yt_module = types.ModuleType("youtube_transcript_api")

        class YouTubeTranscriptApi:
            def fetch(self, video_id, languages=None):
                return []

        yt_module.YouTubeTranscriptApi = YouTubeTranscriptApi
        sys.modules["youtube_transcript_api"] = yt_module


_install_groq_stub()
_install_langchain_stubs()
_install_sentence_transformer_stub()
_install_faiss_stub()
_install_bm25_stub()
_install_google_and_youtube_stubs()

# Keep DB configuration calls from failing in tests that do not monkeypatch DB access.
os.environ.setdefault("MONGO_URI_CLOUD", "mongodb://localhost:27017/test")


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fake_products(fixtures_dir):
    return json.loads((fixtures_dir / "fake_products.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def fake_profiles(fixtures_dir):
    return json.loads((fixtures_dir / "fake_profiles.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def fake_feedback(fixtures_dir):
    return json.loads((fixtures_dir / "fake_feedback.json").read_text(encoding="utf-8"))
