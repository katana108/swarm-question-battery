import json
from types import SimpleNamespace

from run_coder import code_chunk, cost_usd, is_done, load_env, parse_json, run

CHUNK = "[2026-01-01T00:00:00Z] A (public):\nhello world"
GOOD = {"answers": [], "chain": {}, "first_break": "none"}


class FakeClient:
    """Stands in for anthropic.Anthropic: replies are queued, calls are recorded."""

    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text, stop = self.replies.pop(0)
        usage = SimpleNamespace(input_tokens=1000, output_tokens=2000, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], usage=usage, stop_reason=stop)


def make_dirs(tmp_path, n=3):
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    ids = [f"m{i:03d}" for i in range(n)]
    for i in ids:
        (in_dir / f"{i}.txt").write_text(CHUNK)
    return in_dir, tmp_path / "out", ids


def test_parse_json_handles_fence_and_chatter():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Here you go: {"a": 1} done') == {"a": 1}
    assert parse_json("no json here") is None
    assert parse_json("{broken") is None


def test_cost_usd():
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=1_000_000, cache_read_input_tokens=1_000_000, cache_creation_input_tokens=0)
    assert abs(cost_usd(usage) - (2.0 + 10.0 + 0.2)) < 1e-9


def test_code_chunk_caches_prefix_and_flags_refusal():
    client = FakeClient([(json.dumps(GOOD), "end_turn"), ("", "refusal")])
    result, cost, status = code_chunk(client, "m", CHUNK)
    blocks = client.calls[0]["messages"][0]["content"]
    assert status == "ok" and result["first_break"] == "none" and cost > 0
    assert blocks[0]["cache_control"] == {"type": "ephemeral"} and "hello world" in blocks[1]["text"]
    assert "hello world" not in blocks[0]["text"]  # the chunk stays out of the cached part
    assert code_chunk(client, "m", CHUNK)[2] == "refusal"


def test_run_saves_skips_done_and_logs_problems(tmp_path):
    in_dir, out_dir, ids = make_dirs(tmp_path)
    client = FakeClient([(json.dumps(GOOD), "end_turn"), ("not json", "end_turn"), (json.dumps(GOOD), "end_turn")])
    run(client, "m", in_dir, out_dir, ids, cap_usd=10, workers=1)
    log = json.loads((out_dir / "cost_log.json").read_text())
    assert log["problems"] == {"m001": "bad_json"} and log["calls"] == 3
    assert is_done(out_dir / "m000.json", CHUNK) and not (out_dir / "m001.json").exists()
    assert json.loads((out_dir / "m000.json").read_text())["chunk_id"] == "m000"
    assert json.loads((out_dir / "coder_meta.json").read_text())["chunks_coded"] == 2

    rerun = FakeClient([(json.dumps(GOOD), "end_turn")])
    run(rerun, "m", in_dir, out_dir, ids, cap_usd=10, workers=1)
    assert len(rerun.calls) == 1  # only the failed chunk is retried
    assert json.loads((out_dir / "cost_log.json").read_text())["problems"] == {}


def test_failed_quote_validation_means_not_done(tmp_path):
    bad = {"answers": [{"q": "Q1", "code": {"us": "same_run"}, "observability": "public",
                        "quotes": [{"text": "words not in the chunk", "speaker_type": "agent"}]}], "chain": {}}
    out = tmp_path / "m000.json"
    out.write_text(json.dumps(bad))
    assert not is_done(out, CHUNK)


def test_spend_cap_stops_calls(tmp_path):
    in_dir, out_dir, ids = make_dirs(tmp_path, n=4)
    one_call = cost_usd(SimpleNamespace(input_tokens=1000, output_tokens=2000))
    client = FakeClient([(json.dumps(GOOD), "end_turn")] * 4)
    run(client, "m", in_dir, out_dir, ids, cap_usd=one_call * 1.5, workers=1)
    assert len(client.calls) == 2  # the cap is checked before each call, so it can overshoot by one call


def test_load_env_does_not_override(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nTEST_KEY_A=from_file\nTEST_KEY_B='quoted'\n")
    monkeypatch.setenv("TEST_KEY_A", "already")
    monkeypatch.delenv("TEST_KEY_B", raising=False)
    load_env(env)
    import os
    assert os.environ["TEST_KEY_A"] == "already" and os.environ["TEST_KEY_B"] == "quoted"
    monkeypatch.delenv("TEST_KEY_B")


def test_client_headers_only_when_workspace_set(monkeypatch):
    from run_coder import client_headers
    monkeypatch.delenv("ANTHROPIC_WORKSPACE_ID", raising=False)
    assert client_headers() == {}
    monkeypatch.setenv("ANTHROPIC_WORKSPACE_ID", "wrkspc_x")
    assert client_headers() == {"anthropic-workspace-id": "wrkspc_x"}
