"""SQLite log and trace links (F12). The coordinator writes; the screen only reads."""
import json
import sqlite3
from datetime import datetime, timezone

from src.config import ROOT

DB_PATH = ROOT / "runs.sqlite"

SCHEMA = """
create table if not exists runs (run_id text primary key, scenario_id text, reader text, agents text,
    outcome text, started text, scenario_json text);
create table if not exists messages (run_id text, msg_id text, round int, sender text, type text,
    blocked_by text, json text, ts text);
create table if not exists note_readings (run_id text, note_id text, reader text, json text, ts text);
create table if not exists reading_decisions (run_id text, note_id text, status text, source text, json text, ts text);
create table if not exists reading_mismatches (run_id text, round int, note_id text, agent text,
    reader_says text, agent_says text, ts text);
create table if not exists rule_checks (run_id text, check_id text, subject text, rule_id text, flight text,
    pass int, hard int, detail text, ts text);
create table if not exists plans (run_id text, source text, json text, ts text);
create table if not exists decisions (run_id text, decision text, who text, ts text);
create table if not exists usage (run_id text, purpose text, model text, input_tokens int, output_tokens int,
    cached int, ts text);
create table if not exists trace_links (run_id text, from_type text, from_id text, to_type text, to_id text);
create table if not exists ops_inbox (msg_no integer primary key autoincrement, airport text, sample text, received_at text,
    source text, channel text, ref text, text text, read_in_run text);
"""


def inbox_add(airport: str, sample: str, source: str, channel: str, ref: str, text: str, path=DB_PATH):
    """Visitor messages: stored as received, read only by a live run."""
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    db.execute("insert into ops_inbox (airport, sample, received_at, source, channel, ref, text) values (?,?,?,?,?,?,?)",
               (airport, sample, now(), source, channel, ref.strip()[:12], text.strip()[:240]))
    db.commit()


def inbox(airport: str, sample: str, queued_only=False, path=DB_PATH) -> list[dict]:
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    db.row_factory = sqlite3.Row
    q = "select * from ops_inbox where airport = ? and sample = ?" + (" and read_in_run is null" if queued_only else "")
    return [dict(r) for r in db.execute(q + " order by msg_no", (airport, sample))]


def inbox_mark_read(msg_nos: list[int], run_id: str, path=DB_PATH):
    db = sqlite3.connect(path)
    db.executemany("update ops_inbox set read_in_run = ? where msg_no = ?", [(run_id, n) for n in msg_nos])
    db.commit()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunLog:
    def __init__(self, run_id: str, path=DB_PATH):
        self.run_id = run_id
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)
        for t in ["runs", "messages", "note_readings", "reading_decisions", "reading_mismatches",
                  "rule_checks", "plans", "decisions", "usage", "trace_links"]:
            self.db.execute(f"delete from {t} where run_id = ?", (run_id,))   # rerun replaces

    @classmethod
    def attach(cls, run_id: str, path=DB_PATH) -> "RunLog":
        """Open an existing run without clearing it (for the supervisor's decision)."""
        log = cls.__new__(cls)
        log.run_id, log.db = run_id, sqlite3.connect(path)
        return log

    def _ins(self, table: str, *vals):
        self.db.execute(f"insert into {table} values ({','.join('?' * (len(vals) + 1))})", (self.run_id, *vals))

    def run(self, s, reader, agents):
        self._ins("runs", s.scenario_id, reader, agents, "RUNNING", now(), s.model_dump_json())

    def outcome(self, outcome: str):
        self.db.execute("update runs set outcome = ? where run_id = ?", (outcome, self.run_id))

    def reading(self, r):
        self._ins("note_readings", r.note_id, r.reader, r.model_dump_json(), now())

    def decision_row(self, d):
        self._ins("reading_decisions", d.note_id, d.status, d.source, d.model_dump_json(), now())

    def mismatch(self, rnd, m):
        self._ins("reading_mismatches", rnd, m.note_id, m.agent, m.reader_says, m.agent_says, now())

    def message(self, m):
        self._ins("messages", m.msg_id, m.round, m.sender, m.type, ",".join(m.blocked_by),
                  m.model_dump_json(by_alias=True), now())

    def checks(self, subject: str, checks) -> list[str]:
        ids = []
        for c in checks:
            cid = f"{subject}:{c.rule_id}:{c.flight or 'PLAN'}"
            self._ins("rule_checks", cid, subject, c.rule_id, c.flight, int(c.passed), int(c.hard), c.detail, now())
            ids.append(cid)
        return ids

    def plan(self, p):
        self._ins("plans", p.source, p.model_dump_json(by_alias=True), now())

    def link(self, from_type, from_id, to_type, to_id):
        self._ins("trace_links", from_type, from_id, to_type, to_id)

    def usage(self, rows):
        for u in rows:
            self._ins("usage", u["purpose"], u["model"], u["input_tokens"], u["output_tokens"], int(u["cached"]), now())

    def decide(self, decision: str, who: str = "supervisor"):
        self._ins("decisions", decision, who, now())
        self.commit()

    def commit(self):
        self.db.commit()


def export(run_id: str, path=DB_PATH) -> dict:
    """Whole run as JSON, trace links included (F12.3)."""
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    out = {}
    for (t,) in db.execute("select name from sqlite_master where type = 'table'"):
        col = "read_in_run" if t == "ops_inbox" else "run_id"
        if t != "sqlite_sequence":
            out[t] = [dict(r) for r in db.execute(f"select * from {t} where {col} = ?", (run_id,))]
    return json.loads(json.dumps(out))
