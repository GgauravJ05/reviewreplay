from audit.reader import read_rows

LOG = """# audit log
2026-11-05T09:00:00\talice\tlogin\tlow

2026-11-05T09:05:00\tbob\tdelete-user\thigh
"""


def test_read_rows_skips_comments_and_blanks(tmp_path):
    p = tmp_path / "a.log"
    p.write_text(LOG)
    rows = list(read_rows(p))
    assert [r.actor for r in rows] == ["alice", "bob"]
    assert rows[1].severity == "high"
