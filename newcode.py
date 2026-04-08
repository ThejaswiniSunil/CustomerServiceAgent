
import os, sys, math, json, calendar as cal_mod
from datetime import datetime, timedelta
import requests
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Config ──────────────────────────────────────────────────────────────────

API_BASE = os.getenv("RESOLVEX_API_URL", "http://localhost:8080")

st.set_page_config(
    page_title="ResolveX Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
  background: #08111d !important;
  color: #f5f9ff !important;
  font-family: 'DM Sans', ui-sans-serif, system-ui, sans-serif !important;
}
[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(circle at 10% 12%, rgba(93,133,255,.12), transparent 26%),
    radial-gradient(circle at 86% 18%, rgba(202,109,255,.08), transparent 22%),
    radial-gradient(circle at 52% 84%, rgba(85,230,255,.05), transparent 28%);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#070e1a 0%,#060b14 100%) !important;
  border-right: 1px solid rgba(121,149,230,.12) !important;
}
[data-testid="stSidebar"] * { color: #deebff !important; }
[data-testid="stSidebar"] .stTextArea textarea {
  background: #0f1728 !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 12px !important;
  color: #f5f9ff !important;
  font-size: .85rem !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
  background: #0f1728 !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 12px !important;
  color: #f5f9ff !important;
}
[data-testid="stMain"] { background: transparent !important; }
.block-container { padding-top: 1.4rem !important; padding-bottom: 4rem !important; }

[data-testid="stMetric"] {
  background: linear-gradient(180deg,rgba(18,27,45,.97),rgba(12,19,33,.97)) !important;
  border: 1px solid rgba(120,150,230,.14) !important;
  border-radius: 20px !important;
  padding: 18px 16px !important;
  box-shadow: 0 18px 42px rgba(0,0,0,.28) !important;
}
[data-testid="stMetricValue"] {
  color: #f5f9ff !important; font-size: 1.9rem !important;
  font-weight: 800 !important; letter-spacing: -.04em !important;
}
[data-testid="stMetricLabel"] { color: #93a6c8 !important; font-size: .82rem !important; font-weight: 600 !important; }

/* ── FAB BUTTON ── */
div.st-key-rx_chat_fab {
  position: fixed !important;
  right: 20px !important;
  bottom: 28px !important;
  z-index: 10000 !important;
  width: 76px !important;
  height: 76px !important;
}
div.st-key-rx_chat_fab > div,
div.st-key-rx_chat_fab [data-testid="stVerticalBlock"] {
  background: transparent !important;
}
div.st-key-rx_chat_fab button {
  width: 76px !important;
  height: 76px !important;
  min-height: 76px !important;
  border-radius: 999px !important;
  padding: 0 !important;
  font-size: 0 !important;
  color: transparent !important;
  text-indent: -9999px !important;
  overflow: hidden !important;
  line-height: 0 !important;
  background: linear-gradient(135deg,#6f93ff,#6d97ff) !important;
  box-shadow: 0 12px 42px rgba(93,133,255,.40), 0 0 34px rgba(93,133,255,.20) !important;
  position: relative !important;
  border: none !important;
}
div.st-key-rx_chat_fab button::before {
  content: "";
  position: absolute;
  inset: 0;
  margin: auto;
  width: 30px;
  height: 30px;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round'>\
<path d='M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z'/>\
</svg>");
}
div.st-key-rx_chat_fab button:hover {
  transform: scale(1.04);
  filter: brightness(1.04) !important;
}

div.st-key-rx_chat_panel {
  position: fixed !important;
  right: 24px !important;
  bottom: 110px !important;
  width: 380px !important;
  height: 580px !important;
  z-index: 9999 !important;
  pointer-events: none;
}
div.st-key-rx_chat_panel > div,
div.st-key-rx_chat_panel [data-testid="stVerticalBlock"],
div.st-key-rx_chat_panel [data-testid="stVerticalBlockBorderWrapper"],
div.st-key-rx_chat_panel .element-container,
div.st-key-rx_chat_panel section {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  pointer-events: auto;
}

.rx-chat-shell {
  background: #0d1628;
  border: 1px solid rgba(93,133,255,.22);
  border-radius: 22px;
  box-shadow: 0 24px 60px rgba(0,0,0,.70);
  overflow: hidden;
  isolation: isolate;
  width: 380px;
  height: 580px;
  display: flex;
  flex-direction: column;
  position: fixed;
  right: 24px;
  bottom: 110px;
  z-index: 9999;
}

.rx-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,.07);
  background: #111e35;                        /* solid, not rgba */
}
.rx-chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rx-chat-header-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #9dff8a;
  box-shadow: 0 0 12px #9dff8a;
}
div[data-testid="stForm"] {
  visibility: hidden !important;
  height: 0 !important;
  overflow: hidden !important;
  position: absolute !important;
  pointer-events: none !important;
}
.rx-chat-header-title {
  color: #f5f9ff;
  font-size: .92rem;
  font-weight: 800;
}
.rx-chat-messages {
  padding: 14px;
  flex: 1;
  overflow-y: scroll;
  overflow-x: hidden;
  background: #080f1c;
  min-height: 0;
}


.rx-chat-form {
  padding: 14px;
  border-top: 1px solid rgba(255,255,255,.07);
  background: #0d1628;
  flex-shrink: 0;
}

.rx-chat-sample-note {
  color: #8fa3c7;
  font-size: .75rem;
  font-weight: 700;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: .08em;
}

/* ── CLOSE BUTTON ── */
div.st-key-rx_chat_close button {
  width: 38px !important;
  height: 38px !important;
  min-height: 38px !important;
  border-radius: 999px !important;
  padding: 0 !important;
  border: 1px solid rgba(255,255,255,.10) !important;
  background: #1a2740 !important;            /* solid */
  color: white !important;
  font-size: 16px !important;
  box-shadow: none !important;
}
div.st-key-rx_chat_close button:hover {
  background: #243451 !important;
}

/* ── GLOBAL BUTTONS ── */
.stButton > button {
  background: linear-gradient(135deg,#5d85ff,#7ca4ff) !important;
  color: white !important; border: none !important;
  border-radius: 14px !important; font-weight: 800 !important;
  padding: 10px 18px !important; transition: .18s ease !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:hover { filter: brightness(1.08) !important; }
.stButton > button[kind="secondary"] {
  background: linear-gradient(180deg,rgba(34,48,79,.95),rgba(24,35,57,.95)) !important;
  border: 1px solid rgba(127,177,255,.16) !important;
}

/* ── EXPANDERS ── */
.streamlit-expanderHeader {
  background: rgba(17,26,45,.95) !important;
  border: 1px solid rgba(255,255,255,.07) !important;
  border-radius: 14px !important; color: #f5f9ff !important;
  font-weight: 700 !important;
}
.streamlit-expanderContent {
  background: rgba(12,19,33,.9) !important;
  border: 1px solid rgba(255,255,255,.05) !important;
  border-top: none !important; border-radius: 0 0 14px 14px !important;
}

/* ── INPUTS ── */
.stSelectbox > div > div, .stTextInput > div > div > input {
  background: #0f1728 !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 12px !important; color: #f5f9ff !important;
}
.stTextArea textarea {
  background: #0f1728 !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 12px !important; color: #f5f9ff !important;
}

/* ── ALERTS ── */
.stSuccess { background: rgba(79,255,176,.07) !important; border: 1px solid rgba(79,255,176,.2) !important; border-radius: 12px !important; }
.stError   { background: rgba(255,107,125,.07) !important; border: 1px solid rgba(255,107,125,.2) !important; border-radius: 12px !important; }
.stInfo    { background: rgba(85,230,255,.07)  !important; border: 1px solid rgba(85,230,255,.2)  !important; border-radius: 12px !important; }
.stWarning { background: rgba(255,202,99,.07)  !important; border: 1px solid rgba(255,202,99,.2)  !important; border-radius: 12px !important; }

[data-testid="stDataFrame"] {
  border: 1px solid rgba(255,255,255,.06) !important;
  border-radius: 14px !important; overflow: hidden !important;
}

hr { border-color: rgba(255,255,255,.07) !important; margin: 1rem 0 !important; }

[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 4px !important; }

[data-testid="stSidebar"] div[role="radiogroup"] > label {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 12px 12px !important;
  border-radius: 14px !important;
  margin-bottom: 6px !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #d6e3fa !important;
  font-weight: 700 !important;
  transition: .15s ease !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
  background: rgba(255,255,255,.05) !important;
  border-color: rgba(255,255,255,.08) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-selected="true"] {
  background: rgba(255,255,255,.08) !important;
  border-color: rgba(255,255,255,.12) !important;
  box-shadow: 0 0 18px rgba(157,255,138,.12);
}
[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"] {
  display: none !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label p::before {
  content: "";
  display: inline-block;
  width: 18px;
  height: 18px;
  margin-right: 10px;
  vertical-align: -3px;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  opacity: .9;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(1) p::before {
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23bed3ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<path d='M3 10.5 12 3l9 7.5'/>\
<path d='M5 9.5V21h14V9.5'/>\
</svg>");
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(2) p::before {
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23bed3ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<circle cx='12' cy='12' r='3'/>\
<path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 .6 1.65 1.65 0 0 0-.33 1V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-.33-1 1.65 1.65 0 0 0-1-.6 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-.6-1 1.65 1.65 0 0 0-1-.33H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1-.33 1.65 1.65 0 0 0 .6-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-.6 1.65 1.65 0 0 0 .33-1V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 .33 1 1.65 1.65 0 0 0 1 .6 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.24.3.44.64.6 1 .16.36.24.74.24 1.12s-.08.76-.24 1.12c-.16.36-.36.7-.6 1z'/>\
</svg>");
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(3) p::before {
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23bed3ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<path d='M9 11h6'/>\
<path d='M9 15h6'/>\
<path d='M10 3H6a2 2 0 0 0-2 2v14l4-3h10a2 2 0 0 0 2-2V8l-6-5z'/>\
<path d='M14 3v5h5'/>\
</svg>");
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(4) p::before {
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23bed3ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<path d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/>\
<path d='M3.3 7 12 12l8.7-5'/>\
<path d='M12 22V12'/>\
</svg>");
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,.03); }
::-webkit-scrollbar-thumb { background: rgba(93,133,255,.35); border-radius: 999px; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── CARD ── */
.rx-card {
  background: linear-gradient(180deg,rgba(18,27,45,.97),rgba(12,19,33,.97));
  border: 1px solid rgba(120,150,230,.14);
  border-radius: 22px; padding: 18px; margin-bottom: 12px;
  box-shadow: 0 18px 42px rgba(0,0,0,.28);
  position: relative; overflow: hidden;
}
.rx-card::before {
  content:""; position:absolute; inset:0;
  background:linear-gradient(180deg,rgba(255,255,255,.03),transparent 40%);
  pointer-events:none;
}
.rx-card-title { font-size:1rem;font-weight:800;color:#f5f9ff;letter-spacing:-.02em;margin-bottom:4px; }
.rx-card-desc  { font-size:.8rem;color:#93a6c8;line-height:1.45;margin-bottom:12px; }

/* ── TRACE / FEED / STATUS / TOOLS ── */
.trace-line {
  display:flex; justify-content:space-between; align-items:center;
  padding:10px 12px; border-radius:12px;
  border:1px solid rgba(255,255,255,.05);
  background:rgba(6,10,18,.5);
  font-size:.83rem; margin-bottom:8px; gap:12px;
}
.trace-left  { color:#d8e6fb; flex:1; }
.trace-right { font-weight:800; color:#abf8ca; white-space:nowrap; }

.feed-item {
  display:flex; gap:10px; padding:10px 12px;
  border-radius:12px; border:1px solid rgba(255,255,255,.05);
  background:rgba(17,24,40,.78); margin-bottom:8px;
}
.feed-dot  { width:8px;height:8px;border-radius:999px;background:#55e6ff;box-shadow:0 0 10px #55e6ff;margin-top:7px;flex:0 0 8px; }
.feed-time { color:#8da2c6;font-size:.72rem;margin-bottom:3px; }
.feed-text { color:#dbe7f7;font-size:.8rem;line-height:1.45; }

.status-item {
  display:flex; gap:10px; align-items:flex-start; padding:10px 12px;
  border-radius:14px; border:1px solid rgba(255,255,255,.06);
  background:rgba(17,24,40,.82); margin-bottom:8px;
}
.status-title { font-size:.85rem;font-weight:800;color:#f5f9ff;margin-bottom:3px; }
.status-text  { font-size:.77rem;color:#93a6c8;line-height:1.45; }
.dot { display:inline-block;width:10px;height:10px;border-radius:999px;margin-top:5px;flex:0 0 10px; }
.dot-pending { background:#7c8aa6; }
.dot-running { background:#55e6ff;box-shadow:0 0 12px #55e6ff; }
.dot-done    { background:#4fffb0;box-shadow:0 0 12px #4fffb0; }
.dot-error   { background:#ff6b7d;box-shadow:0 0 12px #ff6b7d; }

.tool-card {
  padding:14px; border-radius:14px;
  border:1px solid rgba(255,255,255,.06);
  background:rgba(17,24,40,.82); margin-bottom:8px;
}
.tool-head  { display:flex;justify-content:space-between;align-items:center;margin-bottom:8px; }
.tool-title { font-size:.86rem;font-weight:800;color:#f5f9ff; }
.tool-badge { font-size:.72rem;color:#bcecff;border:1px solid rgba(85,230,255,.2);background:rgba(85,230,255,.08);border-radius:999px;padding:4px 8px; }
.tool-text  { font-size:.78rem;line-height:1.5;color:#93a6c8;white-space:pre-wrap;word-break:break-word; }

.rx-pill {
  display:inline-block; border:1px solid rgba(255,255,255,.08);
  background:rgba(17,26,45,.9); border-radius:999px;
  padding:5px 12px; font-size:.75rem; color:#dce7f7; margin:3px;
}

/* ── CALENDAR ── */
.cal-grid { display:grid;grid-template-columns:repeat(7,1fr);gap:8px; }
.cal-day-name { text-align:center;font-size:.72rem;color:#93a6c8;font-weight:700;padding-bottom:6px; }
.cal-cell {
  min-height:70px; border-radius:14px;
  border:1px solid rgba(255,255,255,.05);
  background:rgba(12,18,32,.6); padding:8px;
}
.cal-cell.dim   { opacity:.3; }
.cal-cell.today { border-color:rgba(85,230,255,.35);box-shadow:0 0 14px rgba(85,230,255,.1); }
.cal-date { font-size:.76rem;font-weight:800;color:#dce7f7;margin-bottom:4px; }
.cal-pill {
  border-radius:999px; padding:3px 7px; font-size:.67rem; font-weight:700;
  background:rgba(93,133,255,.18); color:#ddecff;
  border:1px solid rgba(93,133,255,.16);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  display:block;margin-top:3px;
}

/* ── KANBAN ── */
.kanban-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:10px; }
.kan-col {
  border-radius:16px; border:1px solid rgba(255,255,255,.05);
  background:rgba(13,19,33,.72); padding:12px; min-height:220px;
}
.kan-head { display:flex;justify-content:space-between;margin-bottom:10px;font-size:.82rem;font-weight:800;color:#f5f9ff; }
.task-card {
  border-radius:12px; border:1px solid rgba(255,255,255,.05);
  background:rgba(18,27,45,.92); padding:10px; margin-bottom:8px;
}
.task-title { font-size:.8rem;font-weight:800;color:#f5f9ff;margin-bottom:3px; }
.task-sub   { font-size:.72rem;color:#93a6c8;line-height:1.4; }

/* ── CHAT MESSAGES ── */
.chat-msg-user {
  background: linear-gradient(135deg,#5d85ff,#7ca4ff);
  color: white; border-radius: 14px; padding: 10px 14px;
  font-size: .86rem; line-height: 1.5; margin-bottom: 8px;
  max-width: 90%; margin-left: auto; text-align: right;
}
.chat-msg-bot {
  background: #162035;                        /* solid instead of rgba */
  border: 1px solid rgba(255,255,255,.07);
  color: #dbe7f7; border-radius: 14px; padding: 10px 14px;
  font-size: .86rem; line-height: 1.5; margin-bottom: 8px;
}
.chat-msg-sys {
  background: #0d2028;                        /* solid */
  border: 1px solid rgba(85,230,255,.14);
  color: #9ecfdf; border-radius: 14px; padding: 8px 12px;
  font-size: .78rem; font-style: italic; margin-bottom: 8px;
}

/* ── BARS ── */
.bar-row { display:grid;grid-template-columns:130px 1fr 40px;gap:10px;align-items:center;margin-bottom:10px; }
.bar-label { font-size:.84rem;color:#d9e6f7; }
.bar-track { height:14px;border-radius:999px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.02);overflow:hidden; }
.bar-fill  { height:100%;border-radius:999px; }
.bar-value { text-align:right;font-weight:800;font-size:.8rem;color:#f5f9ff; }

.side-label {
  color:#7f90b1;font-size:.71rem;font-weight:800;
  text-transform:uppercase;letter-spacing:.14em;padding:0 4px;margin-top:8px;
}

/* ── PRODUCT CARDS ── */
.product-card {
  border-radius:16px;border:1px solid rgba(255,255,255,.06);
  background:rgba(15,23,40,.86);padding:16px;margin-bottom:12px;
}
.mini-stat {
  border-radius:12px;border:1px solid rgba(255,255,255,.05);
  background:#111a2d;padding:10px;text-align:center;
}
.mini-stat span   { display:block;color:#93a6c8;font-size:.72rem;margin-bottom:5px; }
.mini-stat strong { font-size:.92rem;font-weight:800;color:#f5f9ff; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────

def _default_statuses():
    return [
        {"key":"listener",     "title":"Listener Agent",               "state":"pending", "text":"Waiting for complaint."},
        {"key":"analyst",      "title":"Analyzer Agent",               "state":"pending", "text":"Waiting for eligibility check."},
        {"key":"decision",     "title":"Decision Agent",               "state":"pending", "text":"Waiting for resolution selection."},
        {"key":"database",     "title":"Database",                     "state":"pending", "text":"Waiting for case log."},
        {"key":"notes",        "title":"Notes",                        "state":"pending", "text":"Waiting for notes visibility."},
        {"key":"tasks",        "title":"Tasks",                        "state":"pending", "text":"Waiting for task visibility."},
        {"key":"calendar",     "title":"Calendar",                     "state":"pending", "text":"Waiting for follow-up schedule."},
        {"key":"manufacturer", "title":"Communication / Manufacturer", "state":"pending", "text":"Waiting for manufacturer state."},
        {"key":"tracker",      "title":"Tracking Agent",               "state":"pending", "text":"Tracker not run yet."},
        {"key":"customer",     "title":"Customer Portal",              "state":"pending", "text":"No final response yet."},
    ]

def _default_tools():
    return {
        "notes":        {"title":"Notes",        "badge":"Connected", "body":"No notes loaded yet."},
        "tasks":        {"title":"Tasks",         "badge":"Connected", "body":"No tasks loaded yet."},
        "calendar":     {"title":"Calendar",      "badge":"Connected", "body":"No calendar items loaded yet."},
        "manufacturer": {"title":"Manufacturer",  "badge":"Connected", "body":"No manufacturer data loaded yet."},
        "tracker":      {"title":"Tracker",       "badge":"Connected", "body":"Tracker has not been run yet."},
    }

def _init_state():
    defaults = {
        "chat_messages": [
            {"type":"sys",  "text":"ResolveX chat ready"},
            {"type":"bot",  "text":"Hi! Tell me what happened with your order and I'll help you through it."},
        ],
        "trace_items":       [],
        "activity_items":    [],
        "last_product":      None,
        "last_complaint_id": None,
        "statuses":          _default_statuses(),
        "tool_panels":       _default_tools(),
        "chat_open":         False,
        "sample_choice":     "Custom...",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── API helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def fetch_dashboard() -> dict:
    try:
        r = requests.get(f"{API_BASE}/dashboard", timeout=10); r.raise_for_status()
        return r.json().get("data", r.json()) or {}
    except: return {}

@st.cache_data(ttl=30)
def fetch_complaints() -> list:
    try:
        r = requests.get(f"{API_BASE}/complaints", timeout=10); r.raise_for_status()
        d = r.json(); return d.get("complaints", d.get("data", []))
    except: return []

@st.cache_data(ttl=30)
def fetch_products() -> list:
    try:
        r = requests.get(f"{API_BASE}/products", timeout=10); r.raise_for_status()
        d = r.json(); return d.get("products", d.get("product_stats", d.get("data", [])))
    except: return []

@st.cache_data(ttl=30)
def fetch_pending() -> list:
    try:
        r = requests.get(f"{API_BASE}/manufacturer/pending", timeout=10); r.raise_for_status()
        d = r.json(); return d.get("pending", d.get("pending_contacts", d.get("data", [])))
    except: return []

def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        return r.ok, r.json() if r.ok else {}
    except: return False, {}

def api_post(path, payload):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=90)
        return r.ok, r.json() if r.ok else {}
    except Exception as e: return False, {"error": str(e)}

def check_api() -> bool:
    try: return requests.get(f"{API_BASE}/health", timeout=4).ok
    except: return False

# ── State helpers ────────────────────────────────────────────────────────────

def push_trace(text, status="OK"):
    st.session_state.trace_items.insert(0, {"text": text, "status": status})
    st.session_state.trace_items = st.session_state.trace_items[:8]

def push_activity(text):
    st.session_state.activity_items.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "text": text})
    st.session_state.activity_items = st.session_state.activity_items[:16]

def set_status(key, state, text):
    for s in st.session_state.statuses:
        if s["key"] == key:
            s["state"] = state; s["text"] = text; break

def set_tool(key, body, badge="Connected"):
    if key in st.session_state.tool_panels:
        st.session_state.tool_panels[key]["body"] = body
        st.session_state.tool_panels[key]["badge"] = badge

def append_chat(msg_type, text):
    st.session_state.chat_messages.append({"type": msg_type, "text": text})

def reset_session():
    for k in [
        "chat_messages", "trace_items", "activity_items", "last_product",
        "last_complaint_id", "statuses", "tool_panels",
        "chat_open", "sample_choice"
    ]:
        if k in st.session_state:
            del st.session_state[k]
    _init_state()
    for key in ["chat_input_box", "chat_sample_select"]:
        if key in st.session_state:
            del st.session_state[key]

# ── Derived data ─────────────────────────────────────────────────────────────

def derive_tasks(complaints, pending):
    tasks = []
    for c in complaints:
        base = {
            "id":     c.get("complaint_id", "—"),
            "title":  c.get("product_name", "Unknown"),
            "detail": f"{c.get('issue_type','issue')} · {c.get('urgency_level','?')} urgency"
        }
        if c.get("loop_closed_at"):                                  col = "resolved"
        elif (c.get("resolution","")).lower().find("escalate") >= 0: col = "escalated"
        elif c.get("manufacturer_contacted"):                         col = "waiting"
        else:                                                         col = "review"
        tasks.append({**base, "col": col})
    for m in pending:
        tasks.append({
            "col":    "resolved" if m.get("issue_resolved") else "waiting",
            "id":     m.get("product_name", "—"),
            "title":  f"Manufacturer: {m.get('product_name','Unknown')}",
            "detail": f"Email: {'yes' if m.get('email_sent') else 'no'} · Follow-ups: {m.get('follow_up_count',0)}"
        })
    return tasks[:24]

def derive_calendar_events(complaints, pending):
    events = []
    for c in complaints:
        if not c.get("created_at") or not c.get("estimated_resolution_days"): continue
        try:
            created = datetime.fromisoformat(str(c["created_at"]).replace("Z", "+00:00"))
            due = created + timedelta(days=int(c["estimated_resolution_days"] or 0))
            events.append({"date": due, "label": f"{c.get('product_name','Case')} due"})
        except: pass
    for m in pending:
        base = m.get("updated_at") or m.get("contacted_at") or m.get("created_at")
        if not base: continue
        try:
            d = datetime.fromisoformat(str(base).replace("Z", "+00:00")) + timedelta(days=1)
            events.append({"date": d, "label": f"{m.get('product_name','Manufacturer')} follow-up"})
        except: pass
    return events[:30]

def derive_notes(complaints):
    rows = [
        f"Case {c.get('complaint_id','—')} · {c.get('product_name','?')} · "
        f"{c.get('issue_type','?')} · resolution: {c.get('resolution','pending')}"
        for c in complaints[:5]
    ]
    return "\n".join(rows) if rows else "No recent notes available."

# ── HTML render helpers ──────────────────────────────────────────────────────

def render_trace_html():
    items = st.session_state.trace_items
    if not items:
        return '<div style="color:#93a6c8;font-size:.84rem;padding:4px 0;">No trace yet.</div>'
    rows = ""
    for item in items:
        color = "#abf8ca" if item["status"] == "OK" else "#ff6b7d" if item["status"] == "ERR" else "#55e6ff"
        rows += f'<div class="trace-line"><div class="trace-left">&gt; {item["text"]}</div><div class="trace-right" style="color:{color};">[{item["status"]}]</div></div>'
    return rows

def render_activity_html():
    items = st.session_state.activity_items
    if not items:
        return '<div style="color:#93a6c8;font-size:.84rem;padding:4px 0;">No activity yet.</div>'
    rows = ""
    for item in items:
        rows += f'<div class="feed-item"><div class="feed-dot"></div><div><div class="feed-time">{item["time"]}</div><div class="feed-text">{item["text"]}</div></div></div>'
    return rows

def render_status_html():
    html = ""
    for s in st.session_state.statuses:
        html += (
            f'<div class="status-item">'
            f'<span class="dot dot-{s["state"]}"></span>'
            f'<div><div class="status-title">{s["title"]}</div>'
            f'<div class="status-text">{s["text"]}</div></div></div>'
        )
    return html

def render_tools_html():
    html = ""
    for panel in st.session_state.tool_panels.values():
        body = str(panel["body"])[:600]
        html += (
            f'<div class="tool-card">'
            f'<div class="tool-head"><div class="tool-title">{panel["title"]}</div>'
            f'<div class="tool-badge">{panel["badge"]}</div></div>'
            f'<div class="tool-text">{body}</div></div>'
        )
    return html

def render_bars_html(data: dict):
    if not data:
        return '<div style="color:#93a6c8;font-size:.84rem;">No data available.</div>'
    colors = ["#55e6ff","#ca6dff","#ffca63","#5d85ff","#4fffb0","#ff6b7d"]
    items  = list(data.items())
    max_v  = max((float(v or 0) for _, v in items), default=1) or 1
    html   = ""
    for i, (label, value) in enumerate(items):
        pct   = float(value or 0) / max_v * 100
        color = colors[i % len(colors)]
        html += (
            f'<div class="bar-row">'
            f'<div class="bar-label">{label}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color};box-shadow:0 0 10px {color};"></div></div>'
            f'<div class="bar-value">{value}</div></div>'
        )
    return html

def render_donut_html(data: dict):
    colors = ["#ff6b7d","#5d85ff","#55e6ff","#ffca63","#ca6dff","#4fffb0"]
    items  = [(k, int(v or 0)) for k, v in data.items()] if data else []
    total  = sum(v for _, v in items) or 1
    cx, cy, r, stroke = 110, 100, 68, 26
    circumference = 2 * math.pi * r
    offset  = 0
    circles = ""
    for i, (label, value) in enumerate(items):
        pct   = value / total
        dash  = pct * circumference
        color = colors[i % len(colors)]
        circles += (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}"'
            f' stroke-width="{stroke}" stroke-linecap="round"'
            f' stroke-dasharray="{dash:.2f} {circumference:.2f}"'
            f' stroke-dashoffset="{-offset:.2f}"'
            f' transform="rotate(-90 {cx} {cy})"'
            f' style="filter:drop-shadow(0 0 8px {color});"></circle>'
        )
        offset += dash
    circles += (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none"'
        f' stroke="rgba(255,255,255,.06)" stroke-width="{stroke}"'
        f' stroke-dasharray="{circumference:.2f} {circumference:.2f}"></circle>'
    )
    legend = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;font-size:.82rem;color:#d6e3f6;">'
        f'<span style="width:10px;height:10px;border-radius:999px;background:{colors[i%len(colors)]};'
        f'box-shadow:0 0 10px {colors[i%len(colors)]};flex:0 0 10px;display:inline-block;"></span>'
        f'{label} {value}</div>'
        for i, (label, value) in enumerate(items)
    )
    return (
        f'<div style="display:flex;flex-direction:column;align-items:center;">'
        f'<div style="position:relative;display:inline-block;">'
        f'<svg width="220" height="200" viewBox="0 0 220 200">{circles}'
        f'<text x="{cx}" y="{cy-6}" text-anchor="middle" fill="#f5f9ff" font-size="22" font-weight="800">{total}</text>'
        f'<text x="{cx}" y="{cy+16}" text-anchor="middle" fill="#93a6c8" font-size="11">Issues tracked</text>'
        f'</svg></div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;margin-top:8px;width:100%;">{legend}</div>'
        f'</div>'
    )

def render_calendar_html(complaints, pending):
    today = datetime.now()
    year, month = today.year, today.month
    first_day     = datetime(year, month, 1)
    start_wd      = (first_day.weekday() + 1) % 7
    days_in_month = cal_mod.monthrange(year, month)[1]
    prev_days     = cal_mod.monthrange(year, month - 1 if month > 1 else 12)[1]

    events    = derive_calendar_events(complaints, pending)
    event_map = {}
    for ev in events:
        key = ev["date"].strftime("%Y-%m-%d")
        event_map.setdefault(key, []).append(ev["label"])

    day_names = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    html  = f'<div style="font-weight:800;font-size:.9rem;color:#f5f9ff;margin-bottom:10px;">{today.strftime("%B %Y")}</div>'
    html += '<div class="cal-grid">'
    html += "".join(f'<div class="cal-day-name">{n}</div>' for n in day_names)

    for i in range(42):
        if i < start_wd:
            day_num   = prev_days - start_wd + i + 1
            cell_date = datetime(year, month - 1 if month > 1 else 12, day_num)
            dim       = True
        elif i >= start_wd + days_in_month:
            day_num   = i - (start_wd + days_in_month) + 1
            cell_date = datetime(year, month + 1 if month < 12 else 1, day_num)
            dim       = True
        else:
            day_num   = i - start_wd + 1
            cell_date = datetime(year, month, day_num)
            dim       = False

        key      = cell_date.strftime("%Y-%m-%d")
        is_today = (cell_date.date() == today.date())
        day_evs  = event_map.get(key, [])
        css_cls  = "cal-cell" + (" dim" if dim else "") + (" today" if is_today else "")
        pills    = "".join(f'<div class="cal-pill">{ev}</div>' for ev in day_evs[:2])
        html    += f'<div class="{css_cls}"><div class="cal-date">{day_num}</div>{pills}</div>'

    html += "</div>"
    return html

def render_kanban_html(complaints, pending):
    tasks = derive_tasks(complaints, pending)
    cols  = [
        ("review",    "In Review", "#55e6ff"),
        ("waiting",   "Waiting",   "#ffca63"),
        ("escalated", "Escalated", "#ff6b7d"),
        ("resolved",  "Resolved",  "#4fffb0"),
    ]
    html = '<div class="kanban-grid">'
    for key, label, color in cols:
        items = [t for t in tasks if t["col"] == key]
        cards = "".join(
            f'<div class="task-card">'
            f'<div class="task-title">{t["title"]}</div>'
            f'<div class="task-sub">{t["id"]}</div>'
            f'<div class="task-sub">{t["detail"]}</div></div>'
            for t in items
        ) or '<div style="color:#93a6c8;font-size:.8rem;">No items</div>'
        html += (
            f'<div class="kan-col">'
            f'<div class="kan-head"><span style="color:{color};">{label}</span><span>{len(items)}</span></div>'
            f'{cards}</div>'
        )
    html += '</div>'
    return html

def render_chat_html():
    html = ""
    for msg in st.session_state.chat_messages[-20:]:
        if msg["type"] == "user":
            html += f'<div class="chat-msg-user">{msg["text"]}</div>'
        elif msg["type"] == "bot":
            html += f'<div class="chat-msg-bot">{msg["text"]}</div>'
        else:
            html += f'<div class="chat-msg-sys">{msg["text"]}</div>'
    return html

# ── Optional panel loader ────────────────────────────────────────────────────

def _load_optional_panels(complaints, pending):
    ok, data = api_get("/notes/recent")
    if ok:
        set_tool("notes", json.dumps(data, indent=2)[:400])
        set_status("notes", "done", "Notes loaded from backend.")
    else:
        set_tool("notes", derive_notes(complaints), "Derived")
        set_status("notes", "done", "Notes derived from complaints.")

    ok, data = api_get("/tasks/open-summary")
    if ok:
        set_tool("tasks", json.dumps(data, indent=2)[:400])
        set_status("tasks", "done", "Tasks loaded from backend.")
    else:
        derived = "\n".join(f"{t['title']} — {t['detail']}" for t in derive_tasks(complaints, pending)[:6])
        set_tool("tasks", derived or "No tasks yet.", "Derived")
        set_status("tasks", "done", "Tasks derived from complaints.")

    ok, data = api_get("/calendar/summary")
    if ok:
        set_tool("calendar", json.dumps(data, indent=2)[:400])
        set_status("calendar", "done", "Calendar loaded from backend.")
    else:
        evs = derive_calendar_events(complaints, pending)[:6]
        set_tool("calendar",
                 "\n".join(f"{e['date'].strftime('%Y-%m-%d')} — {e['label']}" for e in evs) or "No upcoming events.",
                 "Derived")
        set_status("calendar", "done", "Calendar derived from complaints.")

    ok, data = api_get("/manufacturer/pending")
    if ok:
        raw = data.get("pending") or data.get("pending_contacts") or data.get("data") or []
        if raw:
            set_tool("manufacturer", json.dumps(raw[:2], indent=2)[:500])
            set_status("manufacturer", "done", "Manufacturer data loaded.")
        else:
            set_tool("manufacturer", "No pending manufacturer escalations.")
            set_status("manufacturer", "done", "No pending escalations.")
    else:
        set_tool("manufacturer", "Manufacturer endpoint unavailable.", "Unavailable")
        set_status("manufacturer", "error", "Manufacturer endpoint unavailable.")

# ── Submit complaint ─────────────────────────────────────────────────────────

def do_submit_complaint(complaint_text, complaints, pending):
    append_chat("user", complaint_text)
    push_trace("Complaint received in customer portal", "OK")
    push_trace("Listener agent extracting fields", "RUN")
    push_activity("Complaint submitted from customer portal")
    set_status("listener", "running", "Parsing complaint text...")
    set_status("analyst",  "pending", "Waiting for eligibility check.")
    set_status("decision", "pending", "Waiting for resolution selection.")
    set_status("database", "pending", "Waiting for case log.")
    set_status("customer", "pending", "Waiting for final response.")
    with st.spinner("ResolveX is processing your complaint..."):
        ok, body = api_post("/complaint", {"complaint": complaint_text})


    if not (ok and body.get("success")):
        set_status("listener", "error", "Complaint submission failed.")
        set_status("customer", "error", "No final response returned.")
        err = body.get("detail") or body.get("error") or "Unknown error"
        append_chat("sys", f"Submission failed: {err}")
        push_trace("Complaint submission failed", "ERR")
        push_activity("Complaint submission failed")
        return

    customer     = body.get("customer_response", {})
    steps_done   = body.get("steps_completed", [])
    decision     = customer.get("decision", "unknown")
    eta          = customer.get("estimated_resolution_days", "unknown")
    complaint_id = body.get("complaint_id")

    st.session_state.last_complaint_id = complaint_id

    set_status("listener", "done", "Complaint parsed successfully.")
    push_trace("Listener extraction completed", "OK")
    push_trace("Analyzer agent checking eligibility", "RUN")
    push_activity("Listener agent completed extraction")

    set_status("analyst", "done" if "analyst" in steps_done else "running", "Eligibility review completed.")
    push_trace("Eligibility review completed", "OK")
    push_trace(f"Decision selected: {decision}", "OK")
    push_activity("Analyzer agent completed review")

    set_status("decision", "done" if "decision" in steps_done else "running",
               f"Decision: {decision}. ETA: {eta} day(s).")
    push_trace("Database updating case", "RUN")
    push_activity(f"Decision selected: {decision}")

    if complaint_id:
        set_status("database", "done", f"Complaint logged with ID {str(complaint_id)[:8]}…")
        push_trace(f"Database updated for complaint {str(complaint_id)[:8]}", "OK")
        push_activity(f"Complaint logged with ID {str(complaint_id)[:8]}")
    else:
        set_status("database", "error", "Complaint ID missing from backend response.")
        push_trace("Complaint ID missing from backend response", "ERR")

    set_status("customer", "done", "Customer response returned.")
    if customer.get("acknowledgement"): append_chat("bot", customer["acknowledgement"])
    if customer.get("resolution"):      append_chat("bot", customer["resolution"])
    if steps_done: append_chat("sys", "Completed stages: " + ", ".join(steps_done))

    push_trace("Customer response returned to chat", "OK")
    push_activity("Customer-facing response returned")

    try:
        fresh = fetch_complaints.__wrapped__()
    except Exception:
        fresh = complaints
    found = next((c for c in fresh if c.get("complaint_id") == complaint_id), None)
    if found:
        st.session_state.last_product = found.get("product_name")

    _load_optional_panels(fresh, pending)

    if st.session_state.last_product:
        set_status("tracker", "pending", f"Tracker ready for {st.session_state.last_product}.")
        set_tool("tracker", f"Tracker ready for: {st.session_state.last_product}\nUse 'Run Tracker' to execute follow-up.")

    st.cache_data.clear()

# ── Load data ────────────────────────────────────────────────────────────────

dashboard  = fetch_dashboard()
complaints = fetch_complaints()
products   = fetch_products()
pending    = fetch_pending()

summary     = dashboard.get("summary", {})
resolution  = dashboard.get("resolution_breakdown", {})
issue_types = dashboard.get("issue_breakdown", {})
total_c     = summary.get("total_complaints", len(complaints))
escalated   = resolution.get("escalate", 0)

def _is_overdue(c):
    try:
        eta = c.get("estimated_resolution_days")
        cr  = c.get("created_at")
        if not eta or not cr or c.get("loop_closed_at"):
            return False
        created = datetime.fromisoformat(str(cr).replace("Z", "+00:00"))
        due     = created + timedelta(days=int(eta))
        now     = datetime.now(due.tzinfo)
        return now > due
    except Exception:
        return False

overdue = sum(1 for c in complaints if _is_overdue(c))
api_ok  = check_api()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;padding:8px 0 16px;">
      <div style="width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,#5d85ff,#7ca3ff);
                  display:grid;place-items:center;font-weight:800;color:white;font-size:1rem;letter-spacing:-.04em;
                  box-shadow:0 0 28px rgba(93,133,255,.3);">RX</div>
      <div>
        <div style="font-weight:800;font-size:1rem;color:#f5f9ff;">ResolveX</div>
        <div style="color:#93a6c8;font-size:.75rem;line-height:1.3;">Autonomous Customer Resolution</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    color_api = "#4fffb0" if api_ok else "#ff6b7d"
    label_api = "API Connected" if api_ok else "API Disconnected"
    st.markdown(f'<div style="font-weight:700;font-size:.85rem;color:{color_api};margin-bottom:4px;">● {label_api}</div>', unsafe_allow_html=True)
    st.caption(f"→ {API_BASE}")

    st.markdown('<div class="side-label" style="margin-top:14px;">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("nav", ["  Overview","  Operations","  Complaints","  Products"], label_visibility="collapsed")

    st.markdown('<hr style="margin:14px 0;">', unsafe_allow_html=True)

# ── MAIN HEADER ──────────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-bottom:6px;">
  <h1 style="margin:0;font-size:1.85rem;font-weight:800;letter-spacing:-.05em;color:#f5f9ff;">
    ResolveX — Autonomous Customer Resolution System
  </h1>
  <p style="margin:8px 0 0;color:#c6d6ee;line-height:1.6;font-size:.94rem;">
    From complaint to closure — understanding issues, evaluating eligibility, coordinating actions,
    escalating manufacturers, and tracking cases until resolution.
  </p>
</div>
""", unsafe_allow_html=True)
st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y  %H:%M:%S')}")
st.markdown("<hr>", unsafe_allow_html=True)

# ── FLOATING CHAT BUTTON ─────────────────────────────────────────────────────

fab_wrap = st.container(key="rx_chat_fab")
with fab_wrap:
    if st.button("", key="rx_chat_fab_btn"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

# ── FLOATING CHAT PANEL ──────────────────────────────────────────────────────
if st.session_state.chat_open:
    samples = [
        "My Voltix Charger overheats after five minutes and stopped working. Order ORD001.",
        "I received the wrong AeroBuds Pro color and the box was already damaged. Order ORD003.",
        "The Nova Blender has a broken motor and makes a burning smell after two uses. Order ORD002.",
        "My headphones stopped charging after only 2 weeks. Very frustrated. Order ORD003.",
    ]
    sample_opts = "".join(f'<option value="{s}">{s[:55]}...</option>' for s in samples)
    chat_body = render_chat_html()

    st.markdown(f"""
    <div class="rx-chat-shell">
      <div class="rx-chat-header">
        <div class="rx-chat-header-left">
          <div class="rx-chat-header-dot"></div>
          <div class="rx-chat-header-title">ResolveX Assistant</div>
        </div>
      </div>
      <div class="rx-chat-messages" id="rx-msgs">{chat_body}</div>
      <div class="rx-chat-form">
        <div class="rx-chat-sample-note">Quick samples</div>
        <select id="rx-sample"
          onchange="document.getElementById('rx-input').value=this.value"
          style="width:100%;background:#0f1728;border:1px solid rgba(255,255,255,.08);
                 border-radius:12px;color:#f5f9ff;padding:8px 10px;font-size:.82rem;
                 margin-bottom:8px;box-sizing:border-box;">
          <option value="">Custom...</option>
          {sample_opts}
        </select>
        <textarea id="rx-input" rows="3" placeholder="Describe your issue here..."
          style="width:100%;background:#0f1728;border:1px solid rgba(255,255,255,.08);
                 border-radius:12px;color:#f5f9ff;padding:10px;font-size:.84rem;
                 resize:none;box-sizing:border-box;font-family:inherit;margin-bottom:8px;"></textarea>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
          <button onclick="rxSubmit()"
            style="background:linear-gradient(135deg,#5d85ff,#7ca4ff);color:white;border:none;
                   border-radius:12px;padding:10px;font-weight:800;cursor:pointer;font-size:.84rem;">Send</button>
          <button onclick="rxAction('reset')"
            style="background:rgba(34,48,79,.95);color:white;border:1px solid rgba(127,177,255,.16);
                   border-radius:12px;padding:10px;font-weight:800;cursor:pointer;font-size:.84rem;">Reset</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
          <button onclick="rxAction('tracker')"
            style="background:rgba(34,48,79,.95);color:white;border:1px solid rgba(127,177,255,.16);
                   border-radius:12px;padding:10px;font-weight:800;cursor:pointer;font-size:.84rem;">Tracker</button>
          <button onclick="rxAction('learning')"
            style="background:rgba(34,48,79,.95);color:white;border:1px solid rgba(127,177,255,.16);
                   border-radius:12px;padding:10px;font-weight:800;cursor:pointer;font-size:.84rem;">Learning</button>
        </div>
        <button onclick="rxAction('refresh')"
          style="width:100%;background:rgba(34,48,79,.95);color:white;
                 border:1px solid rgba(127,177,255,.16);border-radius:12px;padding:10px;
                 font-weight:800;cursor:pointer;font-size:.84rem;box-sizing:border-box;
                 margin-bottom:8px;">🔄 Refresh Data</button>
        <div style="padding:10px 12px;border-radius:14px;
                    border:1px solid rgba(108,140,220,.14);background:#0d1e35;
                    font-size:.76rem;color:#93a6c8;line-height:1.5;">
          Multi-agent complaint understanding, decisioning, escalation, follow-up tracking, calendar and task board.
        </div>
      </div>
    </div>
    <script>
      var m=document.getElementById("rx-msgs");
      if(m) m.scrollTop=m.scrollHeight;

      function rxSubmit(){{
        var txt=document.getElementById("rx-input").value.trim();
        if(txt.length<10){{alert("Please enter at least 10 characters.");return;}}
        var url=new URL(window.parent.location.href);
        url.searchParams.set("rx_action","submit");
        url.searchParams.set("rx_msg", encodeURIComponent(txt));
        window.parent.location.href=url.toString();
      }}

      function rxAction(action){{
        var url=new URL(window.parent.location.href);
        url.searchParams.set("rx_action", action);
        window.parent.location.href=url.toString();
      }}
    </script>
    """, unsafe_allow_html=True)

    # Handle URL action params
    params = st.query_params
    rx_action = params.get("rx_action", "")
    rx_msg = params.get("rx_msg", "")

    if rx_action:
        st.query_params.clear()

        if rx_action == "submit" and rx_msg:
            complaint_text = rx_msg.strip()
            if len(complaint_text) >= 10:
                with st.spinner("Processing your complaint..."):
                    do_submit_complaint(complaint_text, complaints, pending)
            st.rerun()

        elif rx_action == "reset":
            reset_session()
            st.rerun()

        elif rx_action == "tracker":
            prod = st.session_state.last_product
            if prod:
                with st.spinner(f"Tracking {prod}..."):
                    ok, res = api_post("/tracker/run", {"product_name": prod})
                if ok and res.get("success"):
                    set_status("tracker", "done", "Tracker executed successfully.")
                    set_tool("tracker", json.dumps(res.get("result", {}), indent=2)[:500])
                    append_chat("sys", f"Tracker ran for {prod}.")
                    push_trace(f"Tracker completed for {prod}", "OK")
                else:
                    set_status("tracker", "error", "Tracker failed.")
                    push_trace(f"Tracker failed for {prod}", "ERR")
                st.cache_data.clear()
            else:
                append_chat("sys", "Submit a complaint first so the tracker knows which product to follow.")
            st.rerun()

        elif rx_action == "learning":
            with st.spinner("Running learning agent..."):
                ok, res = api_post("/learning/run", {})
            if ok and res.get("success"):
                append_chat("sys", "Learning agent finished successfully.")
                push_trace("Learning agent completed", "OK")
            else:
                append_chat("sys", "Learning endpoint unavailable or failed.")
                push_trace("Learning endpoint unavailable", "ERR")
            st.rerun()

        elif rx_action == "refresh":
            st.cache_data.clear()
            push_activity("Dashboard refreshed")
            st.rerun()
            
# ════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ════════════════════════════════════════════════════════════════════════════

if page == "  Overview":

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Complaints",   total_c)
    c2.metric("Active Cases",       sum(1 for c in complaints if not c.get("loop_closed_at")))
    c3.metric("Resolved",           sum(1 for c in complaints if c.get("loop_closed_at") or c.get("resolution")))
    c4.metric("Escalated",          escalated)
    c5.metric("Manufacturer Cases", len(pending) or summary.get("manufacturer_contacted", 0))
    c6.metric("SLA Overdue",        overdue)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="rx-card"><div class="rx-card-title">AI Thought Trace</div><div class="rx-card-desc">Readable multi-agent workflow progression.</div>', unsafe_allow_html=True)
        st.markdown(render_trace_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="rx-card"><div class="rx-card-title">Live Activity Feed</div><div class="rx-card-desc">Recent operational events and updates.</div>', unsafe_allow_html=True)
        st.markdown(render_activity_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.markdown('<div class="rx-card"><div class="rx-card-title">Resolution Breakdown</div><div class="rx-card-desc">Outcome distribution across complaints.</div>', unsafe_allow_html=True)
        st.markdown(render_bars_html(resolution), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_r2:
        st.markdown('<div class="rx-card"><div class="rx-card-title">Issue Type Distribution</div><div class="rx-card-desc">Current complaint category mix.</div>', unsafe_allow_html=True)
        st.markdown(render_donut_html(issue_types), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE: OPERATIONS
# ════════════════════════════════════════════════════════════════════════════

elif page == "  Operations":

    col_l, col_r = st.columns([1, 1.1])
    with col_l:
        st.markdown('<div class="rx-card"><div class="rx-card-title">System Status</div><div class="rx-card-desc">Real subsystem states during execution.</div>', unsafe_allow_html=True)
        st.markdown(render_status_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="rx-card"><div class="rx-card-title">Operational Panels</div><div class="rx-card-desc">Notes, tasks, calendar, manufacturer, and tracker output.</div>', unsafe_allow_html=True)
        st.markdown(render_tools_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.markdown('<div class="rx-card"><div class="rx-card-title">Calendar</div><div class="rx-card-desc">Estimated due dates and follow-ups.</div>', unsafe_allow_html=True)
        st.markdown(render_calendar_html(complaints, pending), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_r2:
        st.markdown('<div class="rx-card"><div class="rx-card-title">Task Board</div><div class="rx-card-desc">Derived from current case state.</div>', unsafe_allow_html=True)
        st.markdown(render_kanban_html(complaints, pending), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    with st.expander("⚙️ Manual Agent Triggers"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Run Tracker Agent**")
            tracker_products = [p.get("product_name") for p in products
                                if p.get("manufacturer_contacted") and not p.get("manufacturer_resolved")]
            if tracker_products:
                sel = st.selectbox("Product to track:", tracker_products, key="ops_tracker_select")
                if st.button("▶ Run Tracker", key="ops_run_tracker"):
                    with st.spinner(f"Tracking {sel}..."):
                        ok, res = api_post("/tracker/run", {"product_name": sel})
                    if ok and res.get("success"):
                        st.success(f"Tracker completed for {sel}")
                        push_trace(f"Tracker completed for {sel}", "OK")
                        push_activity(f"Tracker completed for {sel}")
                        set_status("tracker", "done", f"Tracker completed for {sel}.")
                        set_tool("tracker", json.dumps(res.get("result",{}), indent=2)[:500])
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.error(f"Failed: {res.get('error')}")
            else:
                st.info("No products awaiting tracker.")
        with c2:
            st.markdown("**Run Learning Agent**")
            if st.button("▶ Run Learning Agent", key="ops_run_learning"):
                with st.spinner("Analyzing patterns..."):
                    ok, res = api_post("/learning/run", {})
                if ok and res.get("success"):
                    st.success("Learning agent completed")
                    push_trace("Learning agent completed", "OK")
                    push_activity("Learning agent completed")
                    st.rerun()
                else:
                    st.error(f"Failed: {res.get('error')}")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: COMPLAINTS
# ════════════════════════════════════════════════════════════════════════════

elif page == "  Complaints":

    st.markdown('<div class="rx-card"><div class="rx-card-title">Complaints</div><div class="rx-card-desc">Filter complaints by product, issue, urgency, and resolution.</div></div>', unsafe_allow_html=True)

    if not complaints:
        st.info("No complaints logged yet.")
    else:
        df = pd.DataFrame(complaints)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            prods = ["All"] + sorted(df["product_name"].dropna().unique().tolist()) if "product_name" in df.columns else ["All"]
            pf = st.selectbox("Product", prods, key="cp_prod")
        with c2:
            ress = ["All"] + sorted(df["resolution"].dropna().unique().tolist()) if "resolution" in df.columns else ["All"]
            rf = st.selectbox("Resolution", ress, key="cp_res")
        with c3:
            uf = st.selectbox("Urgency", ["All","high","medium","low"], key="cp_urg")
        with c4:
            issues = ["All"] + sorted(df["issue_type"].dropna().unique().tolist()) if "issue_type" in df.columns else ["All"]
            isf = st.selectbox("Issue Type", issues, key="cp_issue")

        if pf  != "All" and "product_name"  in df.columns: df = df[df["product_name"]  == pf]
        if rf  != "All" and "resolution"    in df.columns: df = df[df["resolution"]    == rf]
        if uf  != "All" and "urgency_level" in df.columns: df = df[df["urgency_level"] == uf]
        if isf != "All" and "issue_type"    in df.columns: df = df[df["issue_type"]    == isf]

        if "created_at" in df.columns:
            df = df.sort_values("created_at", ascending=False)

        display_cols = ["complaint_id","product_name","issue_type","urgency_level",
                        "customer_emotion","resolution","priority","estimated_resolution_days","created_at"]
        existing = [c for c in display_cols if c in df.columns]

        st.dataframe(
            df[existing].rename(columns={
                "complaint_id":"ID","product_name":"Product","issue_type":"Issue",
                "urgency_level":"Urgency","customer_emotion":"Emotion","resolution":"Resolution",
                "priority":"Priority","estimated_resolution_days":"ETA (days)","created_at":"Created"
            }),
            use_container_width=True, hide_index=True,
        )
        st.caption(f"Showing {len(df)} of {len(complaints)} complaints")

# ════════════════════════════════════════════════════════════════════════════
# PAGE: PRODUCTS
# ════════════════════════════════════════════════════════════════════════════

elif page == "  Products":

    st.markdown('<div class="rx-card"><div class="rx-card-title">Products</div><div class="rx-card-desc">Product-level complaint and escalation monitoring.</div></div>', unsafe_allow_html=True)

    if not products:
        st.info("No product data yet.")
    else:
        for prod in products:
            name    = prod.get("product_name", "Unknown")
            total_p = prod.get("total_complaints", 0)
            cont    = prod.get("manufacturer_contacted", False)
            res     = prod.get("manufacturer_resolved", False)
            pattern = prod.get("pattern_detected", False)

            icon   = "✅" if res else ("📨" if cont else ("⚠️" if pattern else "👁️"))
            status = "Resolved" if res else ("Manufacturer Contacted" if cont else ("Pattern Detected" if pattern else "Monitoring"))
            sc     = "#4fffb0" if res else ("#ffca63" if cont else ("#ff6b7d" if pattern else "#55e6ff"))

            st.markdown(f"""
            <div class="product-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                <div>
                  <div style="font-size:.96rem;font-weight:800;color:#f5f9ff;margin-bottom:4px;">{icon} {name}</div>
                  <div style="color:#93a6c8;font-size:.8rem;">{status}</div>
                </div>
                <span class="rx-pill" style="border-color:{sc}40;color:{sc};">{status}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;">
                <div class="mini-stat"><span>Total Complaints</span><strong>{total_p}</strong></div>
                <div class="mini-stat"><span>Pattern Detected</span><strong>{"Yes" if pattern else "No"}</strong></div>
                <div class="mini-stat"><span>Mfr Contacted</span><strong>{"Yes" if cont else "No"}</strong></div>
                <div class="mini-stat"><span>Mfr Resolved</span><strong>{"Yes" if res else "No"}</strong></div>
              </div>
              <div>
                <span class="rx-pill">Product: {name}</span>
                <span class="rx-pill">Complaints: {total_p}</span>
                <span class="rx-pill">Pattern: {"Detected" if pattern else "No"}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if cont and not res:
                if st.button(f"✅ Mark '{name}' Resolved", key=f"resolve_{name}"):
                    with st.spinner("Closing loop and notifying customers..."):
                        ok, result = api_post("/manufacturer/resolve", {"product_name": name})
                    if ok and result.get("success"):
                        notified = result.get("result", {}).get("customers_notified", 0)
                        st.success(f"✅ Resolved! {notified} customer(s) notified.")
                        push_trace(f"Manufacturer issue resolved for {name}", "OK")
                        push_activity(f"Manufacturer issue resolved for {name}")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")
