from main_sample import candidate_chunks, pick


def _eps():
    def rows(eid, n_agents, n_revs, size=400):
        return [{"episode_id": eid, "rev_id": f"{eid}@{i}", "ts": f"2026-01-01T00:00:{i:02d}Z", "agent": f"a{i % n_agents}", "text": "x" * size} for i in range(n_revs)]
    return {"p1": rows("p1", 3, 6), "p2": rows("p2", 1, 6), "p3": rows("p3", 2, 3), "p4": rows("p4", 2, 5), "big": rows("big", 2, 400, 3000)}


def test_filters_pages_and_caps_chunks():
    pool = candidate_chunks(_eps(), exclude_episodes={"p4"}, cap=3)
    pages = {c["episode_id"] for c in pool}
    assert pages == {"p1", "big"}  # p2 single agent, p3 too few revisions, p4 excluded
    assert sum(c["episode_id"] == "big" for c in pool) == 3


def test_pick_is_deterministic_and_second_is_subset():
    pool = candidate_chunks(_eps(), cap=10)
    s1, sec1 = pick(pool, n=8, share=0.25, seed=0)
    s2, sec2 = pick(pool, n=8, share=0.25, seed=0)
    assert [c["chunk_id"] for c in s1] == [c["chunk_id"] for c in s2] and sec1 == sec2
    assert len(sec1) == 2 and set(sec1) <= set(range(len(s1)))
