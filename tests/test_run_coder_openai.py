import json
from types import SimpleNamespace

from run_coder import run
from run_coder_openai import code_chunk, cost_usd

CHUNK = "[2026-01-01T00:00:00Z] A (public):\nhello world"
GOOD = {"answers": [], "chain": {}, "first_break": "none"}


class FakeOpenAI:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        kind, text = self.replies.pop(0)
        usage = SimpleNamespace(input_tokens=1000, output_tokens=2000, input_tokens_details=SimpleNamespace(cached_tokens=500))
        content = [SimpleNamespace(type="refusal" if kind == "refusal" else "output_text", text=text)]
        return SimpleNamespace(output=[SimpleNamespace(type="message", content=content)], output_text=text if kind != "refusal" else "",
                               usage=usage, status="incomplete" if kind == "incomplete" else "completed")


def test_cost_counts_cached_input_at_the_cheap_rate():
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=1_000_000, input_tokens_details=SimpleNamespace(cached_tokens=500_000))
    assert abs(cost_usd(usage) - (0.05 + 0.005 + 0.5)) < 1e-9


def test_code_chunk_statuses():
    client = FakeOpenAI([("text", json.dumps(GOOD)), ("refusal", "no"), ("text", "not json"), ("incomplete", "{cut")])
    assert code_chunk(client, "m", CHUNK)[2] == "ok"
    assert code_chunk(client, "m", CHUNK)[2] == "refusal"
    assert code_chunk(client, "m", CHUNK)[2] == "bad_json"
    assert code_chunk(client, "m", CHUNK)[2] == "truncated"
    assert "hello world" in client.calls[0]["input"]


def test_run_writes_coder_b_meta(tmp_path):
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    (in_dir / "m000.txt").write_text(CHUNK)
    run(FakeOpenAI([("text", json.dumps(GOOD))]), "gpt-6-luna", in_dir, tmp_path / "out", ["m000"], 10, 1,
        coder_fn=code_chunk, coder="B", tool="openai-api")
    meta = json.loads((tmp_path / "out" / "coder_meta.json").read_text())
    assert meta["coder"] == "B" and meta["model"] == "gpt-6-luna" and meta["chunks_coded"] == 1
