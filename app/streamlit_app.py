"""SkyQueue supervisor screen (F11). Reads the SQLite log; computes nothing about safety."""
import json
import sys
from pathlib import Path

import httpx
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.log import RunLog, export, inbox, inbox_add, inbox_mark_read  # noqa: E402
from src.schemas import Plan  # noqa: E402
from src.sim.demo import AIRPORTS, DEMOS, airport_info, demo_scenario, with_visitor_notes  # noqa: E402

WEB = Path(__file__).parent / "web"
ASSETS = Path(__file__).parent / "assets"
st.set_page_config(page_title="SkyQueue", page_icon=str(ASSETS / "Logo" / "skyqueue-mark.svg"), layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Anybody:wdth,wght@50..150,400..900&family=Spline+Sans+Mono:wght@500;700&display=swap');
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #121315; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"] { display: none; }
.block-container { padding: 20px 1.5rem 0; max-width: 1480px; }
.st-key-decisions { display: none; }
.st-key-navbar { position: fixed; top: 0; left: 0; right: 0; z-index: 999980; height: 64px; }
.st-key-navbar iframe { height: 64px !important; }
.st-key-nav { position: fixed; top: 12px; right: 28px; z-index: 999990; width: min(940px, calc(100vw / var(--z, 1) - 600px)) !important; background: transparent; border: 0; padding: 0; }
.st-key-nav [data-testid="stHorizontalBlock"] { gap: 10px !important; align-items: center; flex-wrap: nowrap; }
.st-key-nav [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-nav [data-testid="stElementContainer"], .st-key-nav [data-testid="stMarkdownContainer"] p { margin: 0 !important; }
.st-key-nav [data-baseweb="input"] { height: 40px; border-radius: 6px; }
.st-key-nav [data-testid="stTextInput"] input { height: 36px; background: #121315; font-family: 'Spline Sans Mono', monospace; font-size: 13px; }
.st-key-nav [data-baseweb="input"] { border: 2px solid #ffd400 !important; background: #121315; }
.st-key-nav button { height: 40px !important; min-height: 40px !important; border-radius: 6px !important; padding: 0 16px !important; white-space: nowrap; }
.st-key-nav [data-testid="stPopover"] button { width: 40px; padding: 0 !important; }
.keytoggle { height: 40px; box-sizing: border-box; user-select: none; margin-top: -16px; }
.st-key-nav [data-testid="stMarkdownContainer"], .st-key-nav .stMarkdown { display: flex; align-items: center; height: 40px; }
.st-key-nav [data-testid="stColumn"] { display: flex; align-items: center; }
.st-key-airport_pills button, [data-testid="stPills"] button { font: 700 14px 'Spline Sans Mono', monospace !important; padding: 8px 14px !important; }
[data-testid="stButtonGroup"] > div { flex-wrap: wrap !important; overflow: visible !important; row-gap: 8px; }
.sqload { position: fixed; inset: 0; z-index: 999995; background: #121315f2; display: flex; align-items: center; justify-content: center;
  animation: sqfade .25s ease-out; font-family: 'Anybody', sans-serif; color: #f2f0ea; }
@keyframes sqfade { from { opacity: 0; } }
.sql-box { width: min(560px, 90vw); text-align: center; }
.sql-brand { font: 900 30px 'Anybody', sans-serif; font-stretch: 118%; text-transform: uppercase; } .sql-brand span { color: #ffd400; }
.sql-to { margin: 22px 0 18px; } .sql-to small { display: block; font: 700 12px 'Spline Sans Mono', monospace; letter-spacing: .16em; text-transform: uppercase; color: #8d9097; }
.sql-to b { display: block; font: 900 84px/1 'Anybody', sans-serif; font-stretch: 120%; color: #ffd400; } .sql-to em { font-style: normal; font-size: 18px; color: #cfd0d3; }
.sql-rwy { position: relative; height: 44px; margin: 0 auto 16px; border-radius: 4px; background:
  radial-gradient(circle, #ffd400 0 3px, transparent 4px) 0 4px / 26px 10px repeat-x, radial-gradient(circle, #ffd400 0 3px, transparent 4px) 0 34px / 26px 10px repeat-x,
  linear-gradient(#ffffffaa, #ffffffaa) 0 21px / 100% 2px no-repeat, #0b0c0d; animation: sqlights .6s linear infinite; overflow: hidden; }
@keyframes sqlights { to { background-position: 26px 4px, 26px 34px, 0 21px, 0 0; } }
.sql-plane { position: absolute; top: 4px; left: -40px; font-size: 30px; color: #f2f0ea; animation: sqtaxi 2.2s cubic-bezier(.5,0,.4,1) infinite; text-shadow: -10px 0 14px #ff6b1a; }
@keyframes sqtaxi { to { left: 105%; } }
.sqload p { margin: 0; font-size: 15px; color: #8d9097; }
.block-container { zoom: var(--z, 1); }
.st-key-nav [data-testid="InputInstructions"] { display: none; }
.bigscreen { display: none; }
@media (max-width: 759px) { .bigscreen { display: flex; position: fixed; inset: 0; z-index: 1000000; background: #121315; color: #f2f0ea; flex-direction: column; align-items: center; justify-content: center; gap: 14px; padding: 32px; text-align: center; font-family: 'Anybody', sans-serif; } .bigscreen b { font: 900 34px 'Anybody', sans-serif; font-stretch: 118%; text-transform: uppercase; } .bigscreen b span { color: #ffd400; } .bigscreen p { max-width: 30em; font-size: 17px; line-height: 1.5; color: #cfd0d3; margin: 0; } }
@media (max-width: 1400px) { .keytoggle .kt { display: none; } .st-key-nav button[kind="primary"] { font-size: 12px !important; padding: 0 10px !important; } }
.st-key-bridge { display: none; }
.keytoggle { display: flex; align-items: center; gap: 8px; padding: 0 12px 0 8px; border-radius: 6px; font: 700 11px 'Spline Sans Mono', monospace; letter-spacing: .08em; text-transform: uppercase; white-space: nowrap; }
.keytoggle .knob { width: 34px; height: 18px; border-radius: 999px; position: relative; flex: none; }
.keytoggle .knob::after { content: ""; position: absolute; top: 2px; width: 14px; height: 14px; border-radius: 50%; background: #f2f0ea; transition: left .3s; }
.keytoggle.off { background: #ffffff10; color: #8d9097; } .keytoggle.off .knob { background: #44464c; } .keytoggle.off .knob::after { left: 2px; }
.keytoggle.on { background: #5ccf8a22; color: #5ccf8a; } .keytoggle.on .knob { background: #5ccf8a; } .keytoggle.on .knob::after { left: 18px; }
[data-testid="stHeader"] { display: none; }
.st-key-nav button[kind="primary"] { background: #ffd400 !important; color: #121315 !important; border: 0 !important; font: 800 14px 'Anybody', sans-serif !important;
  text-transform: uppercase; box-shadow: none; }
.st-key-setup, .st-key-livecard, .st-key-addmsg { background: #1b1c1f; border: 1px solid #ffffff14; border-radius: 6px; padding: 18px 20px; }
.st-key-addmsg { border-top: 4px solid #6aa8ff; }
iframe { border: 0; display: block; }
.stButton button, .stDownloadButton button { font-family: 'Spline Sans Mono', monospace; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.stButton button[kind="primary"] { color: #121315; }
.setup-h { font: 900 26px 'Anybody', sans-serif; font-stretch: 118%; text-transform: uppercase; margin: 0 0 4px; color: #f2f0ea; }
.setup-h span { color: #ffd400; }
.nowat { display: flex; align-items: center; gap: 12px; margin: 10px 0 12px; padding: 12px 14px; border: 2px solid #ffd400; border-radius: 8px; background: #ffd40012; }
.nowat .pin { font-size: 26px; } .nowat small { display: block; font: 700 10px 'Spline Sans Mono', monospace; letter-spacing: .12em; text-transform: uppercase; color: #8d9097; }
.nowat b { font: 900 34px/1 'Anybody', sans-serif; font-stretch: 118%; color: #ffd400; margin-right: 10px; } .nowat em { font-style: normal; font-size: 16px; color: #f2f0ea; }
.dset { margin-top: 14px; padding: 12px 14px; background: #121315; border-radius: 6px; border: 1px solid #ffffff14; }
.dset-h { font: 700 11px 'Spline Sans Mono', monospace; letter-spacing: .12em; text-transform: uppercase; color: #5ccf8a; margin-bottom: 8px; }
.dchip { display: flex; align-items: center; gap: 10px; padding: 6px 0; font-size: 14px; color: #cfd0d3; }
.dchip svg { width: 22px; height: 22px; flex: none; } .dchip b { font-family: 'Spline Sans Mono', monospace; color: #f2f0ea; margin-right: 6px; }
.st-key-setup { border-top: 4px solid #ffd400 !important; padding-bottom: 22px !important; margin-bottom: -6px; }
.st-key-decisions, .st-key-bridge { position: absolute !important; height: 0 !important; overflow: hidden; } .setup-p { color: #cfd0d3; margin: 0 0 12px; font-size: 15px; }
.wx { background: #232428; border-radius: 6px; padding: 14px 16px; color: #f2f0ea; font-family: 'Anybody', sans-serif; }
.wx .cat { display: inline-block; font: 800 13px 'Spline Sans Mono', monospace; padding: 3px 9px; border-radius: 3px; color: #121315; }
.wx .big { font: 900 30px 'Anybody', sans-serif; font-stretch: 112%; }
.wx .raw { font: 500 11px 'Spline Sans Mono', monospace; color: #6c7078; margin-top: 10px; word-break: break-all; }
.wx .whead { display: flex; justify-content: space-between; align-items: center; }
.wx .cat { font-size: 16px !important; padding: 5px 12px !important; }
.wx .wcat { color: #8d9097; font-size: 14px; margin: 2px 0 10px; }
.wx .wrow { display: grid; grid-template-columns: 34px 120px 1fr; align-items: center; padding: 9px 0; border-top: 1px solid #ffffff12; font-size: 17px; }
.wx .wic svg { width: 22px; height: 22px; display: block; }
.wx .wl { color: #8d9097; font: 700 12px 'Spline Sans Mono', monospace; letter-spacing: .1em; text-transform: uppercase; }
.wx .wv { font: 700 17px 'Spline Sans Mono', monospace; color: #f2f0ea; }
.wx .wnow { margin-top: 10px; padding: 10px 12px; border-radius: 4px; font-weight: 700; font-size: 15px; }
.wsrc { display: grid; grid-template-columns: 90px 1fr; row-gap: 4px; margin: 10px 0 18px; font-size: 14px; color: #cfd0d3; }
.wsrc span { font: 700 11px 'Spline Sans Mono', monospace; letter-spacing: .1em; text-transform: uppercase; color: #8d9097; padding-top: 2px; }
.wsrc a { color: #ffd400; }
.wx .wnow.calm { background: #5ccf8a1f; color: #5ccf8a; } .wx .wnow.storm { background: #ff5a4e26; color: #ff8a80; }
</style>""", unsafe_allow_html=True)

PLAIN = {"WAKE-01": "aircraft too close on the runway", "RATE-01": "too many departures for the storm rate",
         "TAXI-01": "taxiway over capacity", "FUEL-01": "a flight runs short of fuel", "DUTY-01": "a crew runs out of hours",
         "GATE-01": "a gate isn't free for its inbound", "GATE-02": "a plane waits at a gate with no power",
         "CREW-01": "no ramp crew on shift", "PLAN-01": "the plan is malformed"}
MODELS = {"Claude API": ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"],
          "OpenRouter": ["anthropic/claude-opus-5.5", "anthropic/claude-sonnet-5.5", "anthropic/claude-haiku-5.5"]}
CHANNEL = {"Crew": "ACARS", "Ramp": "Ramp radio", "Dispatch": "Ops chat", "Pilot report": "PIREP", "Ops chat": "Ops chat",
           "You": "Web form", "Supervisor": "Web form"}
CAT_COLOUR = {"VFR": "#5ccf8a", "MVFR": "#6aa8ff", "IFR": "#ff5a4e", "LIFR": "#d36bff"}
CAT_MEANING = {"VFR": "Visual flight rules: clear, good visibility", "MVFR": "Marginal: lower cloud or haze",
               "IFR": "Instrument rules: low cloud or poor visibility", "LIFR": "Low instrument rules: very low cloud or fog"}
_s = 'fill="none" stroke="#ffd400" stroke-width="2" stroke-linecap="round"'
DS_ICON = {
    "db": f'<svg viewBox="0 0 24 24" {_s}><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>',
    "pin": f'<svg viewBox="0 0 24 24" {_s}><path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    "plane": f'<svg viewBox="0 0 24 24" {_s}><path d="M2 13l8-2 4-8 2 1-2 7 6 1 2-2h2l-2 4 2 4h-2l-2-2-6 1 2 7-2 1-4-8-8-2z"/></svg>',
}
WX_ICON = {
    "thermo": f'<svg viewBox="0 0 24 24" {_s}><path d="M10 4a2 2 0 0 1 4 0v10a4 4 0 1 1-4 0z"/><path d="M12 9v7"/></svg>',
    "wind": f'<svg viewBox="0 0 24 24" {_s}><path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8"/></svg>',
    "eye": f'<svg viewBox="0 0 24 24" {_s}><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    "cloud": f'<svg viewBox="0 0 24 24" {_s}><path d="M7 18a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1A4 4 0 1 1 17 18z"/></svg>',
    "clock": f'<svg viewBox="0 0 24 24" {_s}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
}
live = st.session_state.setdefault("live", {})   # (airport, sample) -> (run_id, model)


def plain(rule: str) -> str:
    return PLAIN.get(rule, f"breaks ops note {rule.removeprefix('NOTE-')}" if rule.startswith("NOTE-") else rule)


@st.cache_data(show_spinner=False)
def _run(name: str, airport: str) -> str:
    from src.agents.fake import FakeAgents
    from src.agents.readers import FakeReader
    from src.coordinator import Coordinator

    s = demo_scenario(name, airport)
    log = RunLog(f"{name}-{s.scenario_id}")
    Coordinator(s, FakeReader(), FakeAgents(DEMOS[name]["mode"]), log).run()
    return log.run_id


@st.cache_data(ttl=600, show_spinner=False)
def weather(icao: str) -> dict | None:
    try:
        r = httpx.get("https://aviationweather.gov/api/data/metar", params={"ids": icao, "format": "json"}, timeout=6)
        return (r.json() or [None])[0]
    except Exception:
        return None


def run_live(name: str, airport: str, creds: dict, models: dict) -> str:
    from src.agents.claude import ClaudeAgents
    from src.agents.readers import ClaudeReader
    from src.coordinator import Coordinator

    queued = inbox(airport, name, queued_only=True)
    rows = [dict(source=r["source"], ref=r["ref"], text=r["text"], received=r["received_at"][11:16]) for r in queued]
    s = with_visitor_notes(demo_scenario(name, airport), rows)
    log = RunLog(f"live-{name}-{s.scenario_id}")
    Coordinator(s, ClaudeReader(models["READER"], creds), ClaudeAgents(models["TOWER"], creds, models), log).run()
    inbox_mark_read([r["msg_no"] for r in queued], log.run_id)
    return log.run_id


def current_run(name: str, airport: str) -> str:
    return live[(airport, name)][0] if (airport, name) in live else _run(name, airport)


def sample(name: str, airport: str) -> dict:
    data = export(current_run(name, airport))
    sc = json.loads(data["runs"][0]["scenario_json"])
    plan = Plan.model_validate_json(data["plans"][-1]["json"])
    msgs = [json.loads(m["json"]) for m in data["messages"]]
    decisions = [json.loads(d["json"]) for d in data["reading_decisions"]]
    readings = {r["note_id"]: json.loads(r["json"]) for r in data["note_readings"]}
    timing, by_id = {t.flight: t for t in plan.timing}, {m["msg_id"]: m for m in msgs}
    flights = []
    for f in sc["flights"]:
        ln = next(x for x in plan.lines if x.flight == f["flight"])
        t, hard, src = timing[f["flight"]], [c for c in ln.checks if c.hard], by_id.get(ln.proposed_in)
        flights.append(dict(
            id=f["flight"], gate=f["gate"], power=f["gate_power"], ready=f["ready"], burn=f["burn_kg_min"],
            today_wo=f["real_wheels_off"], today_taxi=f["real_taxi_out"], plan_push=t.push, plan_wo=t.wheels_off,
            plan_taxi=round(t.taxi_min), action=ln.action, until=ln.until, stand=ln.gate if ln.action == "REASSIGN_GATE" else None,
            proposer=src["from"] if src else "BACKUP", round=src["round"] if src else None,
            agreed_by=ln.agreed_by, notes=ln.notes_used, total=len(hard), **{"pass": sum(c.passed for c in hard)},
            fails=sorted({c.rule_id for c in ln.checks if not c.passed and c.hard})))
    notes = []
    for n in sc["notes"]:
        d = next(x for x in decisions if x["note_id"] == n["note_id"] and x["source"] != "AGENT")
        r = readings.get(n["note_id"], {})
        src = n.get("source") or ("You" if n["truth"]["kind"] == "visitor" else "Ops chat")
        notes.append(dict(id=n["note_id"], text=n["text"], status=d["status"], type=d["type"],
                          target=d["flight"] or d["gate"] or "", p_type=r.get("p_type", 0), p_override=r.get("p_override", 0),
                          yours=n["truth"]["kind"] == "visitor", source=src, channel=CHANNEL.get(src, "Ops chat"),
                          received=n.get("received") or "", ref=", ".join(n["flights"] + n["gates"])))
    queued = [dict(id=f"Q{r['msg_no']}", text=r["text"], ref=r["ref"], status="QUEUED", type="NONE", target=r["ref"],
                   p_type=0, p_override=0, yours=True, source=r["source"], channel=r["channel"],
                   received=r["received_at"][11:16] + " UTC") for r in inbox(airport, name, queued_only=True)]
    hard = [c for c in plan.checks if c.hard]
    fails = sorted({c.rule_id for c in hard if not c.passed})
    decided = data["decisions"][-1] if data["decisions"] else None
    info = airport_info(airport)
    return dict(
        name=DEMOS[name]["name"].format(city=info["city"]), blurb=DEMOS[name]["blurb"], icon=DEMOS[name]["icon"],
        airport_name=info["name"], date=sc["date"], rate=sc["rate_per_15"], normal_taxi=sc["normal_taxi"],
        t0=min(f["ready"] for f in flights) - 3,
        t1=max(max(f["today_wo"] for f in flights), max(f["plan_wo"] for f in flights)) + 3,
        flights=flights, notes=notes, queued=queued, fuel_total_before=sum(f["today_taxi"] * f["burn"] for f in flights),
        live=live[(airport, name)][1] if (airport, name) in live else None,
        messages=[dict(round=m["round"], type=m["type"], say=m["rationale"], blocked=bool(m["blocked_by"]), blocked_ids=m["blocked_by"], has_plan=bool(m["lines"]),
                       blocked_text="; ".join(plain(r) for r in m["blocked_by"]), **{"from": m["from"]}) for m in msgs],
        outcome=dict(source=plan.source, round=max(m["round"] for m in msgs)),
        can_approve=not fails and all(ln.checks for ln in plan.lines),
        checks_pass=sum(c.passed for c in hard), checks_total=len(hard), fails=[plain(r) for r in fails],
        decided=f"{decided['decision'].capitalize()} at {decided['ts'][11:16]} UTC" if decided else None)


def page(name: str, data) -> str:
    html = (WEB / name).read_text(encoding="utf-8")
    for tag, f in (("/*BASE*/", "base.css"), ("/*APP*/", "app.css")):
        html = html.replace(tag, (WEB / f).read_text(encoding="utf-8"))
    html = html.replace("<!--SYMBOLS-->", (WEB / "symbols.html").read_text(encoding="utf-8") + (WEB / "sprites.html").read_text(encoding="utf-8"))
    html = html.replace("<!--ARCH-->", (WEB / "arch.html").read_text(encoding="utf-8")) if "<!--ARCH-->" in html else html
    return html.replace("/*DATA*/", json.dumps(data))


airport = st.session_state.setdefault("airport", AIRPORTS[0])
info = airport_info(airport)

# hidden buttons: the story page clicks these so every decision lands in the audit log
with st.container(key="decisions"):
    for name in DEMOS:
        for what in ("APPROVE", "REJECT"):
            if st.button(f"{what}::{airport}::{name}"):
                RunLog.attach(current_run(name, airport)).decide(f"{what}D")

loading = st.empty()
if st.session_state.get("loaded_airport") != airport:
    loading.markdown(f"""<div class="sqload"><div class="sql-box">
<div class="sql-brand">Sky<span>Queue</span></div>
<div class="sql-to"><small>Taxiing to</small><b>{airport}</b><em>{info["name"]}</em></div>
<div class="sql-rwy"><span class="sql-plane">✈</span></div>
<p>Loading three real storm days from the 2015 data, the ops inbox and the agents' plans…</p>
</div></div>""", unsafe_allow_html=True)
samples = {k: sample(k, airport) for k in DEMOS}
st.session_state.loaded_airport = airport
loading.empty()

st.markdown('<div class="bigscreen"><b>Sky<span>Queue</span></b><p>SkyQueue needs a bigger screen. Open it on a laptop or desktop or widen this window.</p></div>', unsafe_allow_html=True)

# ---------- pinned header ----------
with st.container(key="navbar"):
    components.html(page("nav.html", {"code": airport, "city": info["city"]}), height=64, scrolling=False)

# ---------- hero ----------
components.html(page("hero.html", dict(order=list(DEMOS), airport=info["city"],
                                       samples={k: {x: v[x] for x in ("name", "blurb", "icon")} for k, v in samples.items()})),
                height=664, scrolling=False)

# ---------- your setup: airport, flight, live weather ----------
with st.container(key="setup"):
    left, right = st.columns([1, 1.3], gap="large")
    with left:
        st.markdown(f'''<p class="setup-h">Choose your <span>airport</span></p>
<div class="nowat"><span class="pin">📍</span><div><small>Now showing</small><b>{airport}</b><em>{info["name"]}</em></div></div>
<p class="setup-p">Click an airport below. These are the 8 airports with the most delayed departures in the data; each sample replays one of its real storm days.</p>
''', unsafe_allow_html=True)
        pick = st.pills("Airport", AIRPORTS, default=airport, key="airport_pills", label_visibility="collapsed",
                        format_func=lambda c: f"{c}  {airport_info(c)['city']}")
        if pick and pick != airport:
            st.session_state.airport = pick
            st.rerun()
        st.markdown(f'''<div class="dset"><div class="dset-h">Built on the challenge dataset</div>
<div class="dchip">{DS_ICON["db"]}<span><b>flights.csv</b> 2015 US DOT on-time data, 358,774 delay records</span></div>
<div class="dchip">{DS_ICON["pin"]}<span><b>airports.csv</b> 322 airports</span></div>
<div class="dchip">{DS_ICON["plane"]}<span><b>airlines.csv</b> 14 airlines</span></div></div>''', unsafe_allow_html=True)
        focus = "—"
    with right:
        w = weather(info["icao"])
        if w:
            cat = w.get("fltCat") or "?"
            gust = w.get("wgst") or 0
            stormy = cat in ("IFR", "LIFR") or gust >= 25
            clouds = ", ".join(f"{c['cover']} {c['base']:,} ft" for c in (w.get("clouds") or [])[:2] if c.get("base")) or "Clear"
            rows = [
                ("thermo", "Temperature", f"{w.get('temp', '–')} °C"),
                ("wind", "Wind", f"{w.get('wdir', '–')}° at {w.get('wspd', '–')} kt" + (f", gusts {gust} kt" if gust else "")),
                ("eye", "Visibility", f"{w.get('visib', '–')} miles"),
                ("cloud", "Cloud", clouds),
                ("clock", "Observed", f"{w.get('reportTime', '')[11:16]} UTC"),
            ]
            body = "".join(f'<div class="wrow"><span class="wic">{WX_ICON[i]}</span><span class="wl">{lab}</span><span class="wv">{val}</span></div>'
                           for i, lab, val in rows)
            st.markdown(f'''<div class="wx"><div class="whead"><span class="big">Live at {info["icao"]}</span>
    <span class="cat" style="background:{CAT_COLOUR.get(cat, "#8d9097")}">{cat}</span></div>
    <div class="wcat">{CAT_MEANING.get(cat, "")}</div>{body}
    <div class="wnow {"storm" if stormy else "calm"}">{"⚡ Storm conditions now: SkyQueue would be in use." if stormy else "✓ Calm right now. The samples replay a 2015 storm day."}</div>
    <div class="raw">{w.get("rawOb", "")}</div></div>''', unsafe_allow_html=True)
            st.markdown('<div class="wsrc"><span>Source</span><a href="https://aviationweather.gov" target="_blank">NOAA Aviation Weather Center</a>'
                        '<span>Updates</span>every 10 minutes<span>Used for</span>display only: the samples replay 2015 weather</div>',
                        unsafe_allow_html=True)
        else:
            st.caption("Live weather is unavailable right now.")

# ---------- messages typed into the inbox form arrive through this hidden field ----------
with st.container(key="bridge"):
    raw = st.text_input("bridge", key="bridge_in", label_visibility="collapsed")
if raw:
    try:
        m = json.loads(raw)
        if str(m.get("text", "")).strip() and m.get("to") in DEMOS:
            src = m.get("source") or "You"
            inbox_add(airport, m["to"], src, CHANNEL.get(src, "Web form"), m.get("ref", ""), m["text"])
    except (ValueError, TypeError):
        pass
    del st.session_state["bridge_in"]
    st.rerun()

# ---------- top right: the API key, always in view ----------
with st.container(key="nav"):
    key_on = bool(st.session_state.get("api_key", "").strip())
    a, b, c, d = st.columns([1.2, 3.6, 1.9, .42], vertical_alignment="center")
    a.markdown(f'<div class="keytoggle {"on" if key_on else "off"}"><span class="knob"></span>'
               f'<span class="kt">{"API key on" if key_on else "API key off"}</span></div>', unsafe_allow_html=True)
    b.text_input("API key", key="api_key", type="password", label_visibility="collapsed",
                 placeholder="Paste your Claude or OpenRouter API key",
                 help="Used only for live runs, in this browser session. Never saved, logged or sent anywhere else.")
    go = c.button("▶ Run live with API key", type="primary", disabled=not key_on, use_container_width=True)
    with d.popover("⚙"):
        k = st.session_state.get("api_key", "").strip()
        provider = "OpenRouter" if k.startswith("sk-or-") else "Claude API"
        st.markdown(f"**Provider:** {provider} (from your key)")
        st.markdown("**Model for each agent**")
        models = {}
        for role, label in (("READER", "Note reader"), ("TOWER", "Tower"), ("PILOT", "Pilot"), ("GROUND", "Ground")):
            models[role] = st.selectbox(label, MODELS[provider], key=f"model_{role}",
                                        help="Bigger models reason better; smaller ones answer faster and cost less.")
        workspace = st.text_input("Workspace ID (optional)", help="Only if your Claude key isn't tied to a workspace.") \
            if provider == "Claude API" else None
        which = st.selectbox("Scenario", list(DEMOS), format_func=lambda k: f"{samples[k]['name']}, {airport}", key="livewhich")
        st.caption(f"{len(inbox(airport, which, queued_only=True))} queued inbox message(s) will be read.")
if go:
    k = st.session_state["api_key"].strip()
    creds = {"provider": "openrouter" if k.startswith("sk-or-") else "anthropic", "key": k,
             "workspace": (workspace or "").strip() or None}
    with st.spinner("The note reader and three agents are working…"):
        try:
            used = sorted(set(models.values()))
            label = used[0] if len(used) == 1 else f"{len(used)} models"
            live[(airport, which)] = (run_live(which, airport, creds, models), label)
            st.session_state.autoplay = which
            st.rerun()
        except Exception as e:
            st.error(f"The live run failed ({type(e).__name__}). The recorded scenario still works.")

# runway edge lights switch on when a key goes in or a sample plays
st.markdown("""<style>
.stApp::before, .stApp::after { content: ""; position: fixed; top: 0; bottom: 0; width: 12px; z-index: 999970; pointer-events: none;
  opacity: 0; transition: opacity .9s ease; background: radial-gradient(circle, #ffd400 0 3px, #ffd40033 4px, transparent 6px) 0 0 / 12px 40px;
  animation: rwylights 1.1s linear infinite; filter: drop-shadow(0 0 6px #ffd400); }
.stApp::before { left: 4px; } .stApp::after { right: 4px; }
@keyframes rwylights { to { background-position: 0 40px; } }
html.rwy-lit .stApp::before, html.rwy-lit .stApp::after, .stApp:has(.keytoggle.on)::before, .stApp:has(.keytoggle.on)::after { opacity: 1; }
.stApp:has(.keytoggle.on) .st-key-nav [data-baseweb="input"] { border-color: #5ccf8a !important; box-shadow: 0 0 16px #5ccf8a66; }div[role="dialog"] { background: #1b1c1f; border: 2px solid #ffd400; }
.welcome-h { font: 900 34px/1 'Anybody', sans-serif; font-stretch: 118%; text-transform: uppercase; color: #f2f0ea; margin: 0 0 8px; }
.welcome-h span { color: #ffd400; }
.welcome-lights { height: 10px; margin: 6px 0 14px; background: radial-gradient(circle, #ffd400 0 3px, transparent 4px) 0 0 / 22px 10px;
  animation: wl 1s linear infinite; filter: drop-shadow(0 0 4px #ffd400); }
@keyframes wl { to { background-position: 22px 0; } }
</style>""", unsafe_allow_html=True)

# ---------- the story ----------
auto = st.session_state.pop("autoplay", None)
order = [auto] + [k for k in DEMOS if k != auto] if auto else list(DEMOS)
components.html(page("story.html", dict(order=order, airport=airport, autoplay=bool(auto),
                                        focus=None if auto or focus == "—" else focus,
                                        samples={k: samples[k] for k in DEMOS})), height=3200, scrolling=False)
