import os
import sys
import math
import json
import html
import calendar as cal_mod
from datetime import datetime

import requests
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── CONFIG ──────────────────────────────────────────────────────────────────

API_BASE = os.getenv("RESOLVEX_API_URL", "http://localhost:8080").rstrip("/")
REQUEST_TIMEOUT = 20

st.set_page_config(
    page_title="ResolveX Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap');

:root {
  --bg: #08111d;
  --panel: rgba(22, 30, 48, 0.88);
  --panel-2: rgba(18, 26, 42, 0.92);
  --line: rgba(255,255,255,.08);
  --text: #f5f9ff;
  --muted: #9aaed0;
  --blue: #7da2ff;
  --cyan: #67e9ff;
  --green: #9dff8a;
  --green-soft: rgba(157,255,138,.22);
}

html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 14% 18%, rgba(125,162,255,.12), transparent 25%),
    radial-gradient(circle at 82% 20%, rgba(103,233,255,.09), transparent 24%),
    linear-gradient(180deg, #07101b 0%, #091321 100%) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', ui-sans-serif, system-ui, sans-serif !important;
}

[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.018) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(to bottom, rgba(255,255,255,.18), transparent 80%);
  opacity: .18;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(10,16,27,.96), rgba(8,12,20,.96)) !important;
  border-right: 1px solid rgba(255,255,255,.06) !important;
  box-shadow: inset -1px 0 0 rgba(255,255,255,.03);
}
[data-testid="stSidebar"] * { color: #deebff !important; }

[data-testid="stMain"] { background: transparent !important; }

.block-container {
  padding-top: 1.35rem !important;
  padding-bottom: 4rem !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,.03); }
::-webkit-scrollbar-thumb { background: rgba(93,133,255,.35); border-radius: 999px; }

#MainMenu, footer { visibility: hidden; }

header,
[data-testid="stHeader"] {
  visibility: visible !important;
  background: #08111d !important;
  border-bottom: 1px solid rgba(255,255,255,.06) !important;
}

[data-testid="stToolbar"] {
  display: block !important;
  right: auto !important;
  left: 12px !important;
  top: 10px !important;
}
[data-testid="stToolbar"] button {
  background: rgba(15,23,40,.96) !important;
  border: 1px solid rgba(255,255,255,.10) !important;
  border-radius: 12px !important;
  color: #dce7f7 !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,.03) inset !important;
}
[data-testid="stToolbar"] button svg {
  fill: #dce7f7 !important;
  stroke: #dce7f7 !important;
}
[data-testid="stToolbar"] button:hover {
  background: rgba(28,40,66,.98) !important;
  border-color: rgba(93,133,255,.22) !important;
}
[data-testid="stToolbar"] * {
  color: #dce7f7 !important;
}

[data-testid="stMetric"] {
  background: linear-gradient(180deg, rgba(34,42,58,.92), rgba(27,35,49,.92)) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 18px !important;
  padding: 18px 16px !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.02) inset,
    0 10px 30px rgba(0,0,0,.28),
    0 0 24px rgba(125,162,255,.08) !important;
  position: relative;
  overflow: hidden;
}
[data-testid="stMetric"]::after {
  content: "";
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 12px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(157,255,138,.7), rgba(125,162,255,.85));
  opacity: .8;
}
[data-testid="stMetricValue"] {
  color: #ffffff !important;
  font-size: 2rem !important;
  font-weight: 800 !important;
  letter-spacing: -.04em !important;
}
[data-testid="stMetricLabel"] {
  color: #d5e1f7 !important;
  font-size: .82rem !important;
  font-weight: 700 !important;
}

.stButton > button {
  background: linear-gradient(135deg, #5f82ff, #85a6ff) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  box-shadow: 0 8px 20px rgba(93,133,255,.25) !important;
  color: white !important;
  border-radius: 14px !important;
  font-weight: 800 !important;
  padding: 10px 18px !important;
  transition: .18s ease !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:hover {
  filter: brightness(1.06) !important;
  transform: translateY(-1px);
}

.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {
  background: #0f1728 !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 12px !important;
  color: #f5f9ff !important;
}

.stSuccess { background: rgba(79,255,176,.07) !important; border: 1px solid rgba(79,255,176,.2) !important; border-radius: 12px !important; }
.stError   { background: rgba(255,107,125,.07) !important; border: 1px solid rgba(255,107,125,.2) !important; border-radius: 12px !important; }
.stInfo    { background: rgba(85,230,255,.07) !important; border: 1px solid rgba(85,230,255,.2) !important; border-radius: 12px !important; }
.stWarning { background: rgba(255,202,99,.07) !important; border: 1px solid rgba(255,202,99,.2) !important; border-radius: 12px !important; }

[data-testid="stDataFrame"] {
  border: 1px solid rgba(255,255,255,.06) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}

hr {
  border-color: rgba(255,255,255,.07) !important;
  margin: 1rem 0 !important;
}

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

.rx-card {
  background: linear-gradient(180deg, rgba(33,41,56,.88), rgba(24,31,44,.9));
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 24px;
  padding: 18px;
  margin-bottom: 14px;
  box-shadow:
    0 16px 40px rgba(0,0,0,.28),
    0 0 0 1px rgba(255,255,255,.02) inset,
    0 0 30px rgba(125,162,255,.08);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(8px);
}
.rx-card.glow-green {
  box-shadow:
    0 16px 40px rgba(0,0,0,.28),
    0 0 0 1px rgba(255,255,255,.03) inset,
    0 0 26px rgba(157,255,138,.18),
    0 0 0 2px rgba(157,255,138,.18);
}
.rx-card.glow-blue {
  box-shadow:
    0 16px 40px rgba(0,0,0,.28),
    0 0 0 1px rgba(255,255,255,.03) inset,
    0 0 26px rgba(103,233,255,.16),
    0 0 0 2px rgba(103,233,255,.12);
}
.rx-card-title {
  font-size: 1rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -.02em;
  margin-bottom: 4px;
}
.rx-card-desc {
  font-size: .82rem;
  color: var(--muted);
  line-height: 1.5;
  margin-bottom: 12px;
}

.trace-line {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:12px 14px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.05);
  background: rgba(10,16,27,.7);
  font-size:.9rem;
  margin-bottom:8px;
  gap:12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  line-height: 1.6;
  color:#dfe9ff;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.02);
}
.trace-left  { color:#d8e6fb; flex:1; }
.trace-right { font-weight:800; color:#abf8ca; white-space:nowrap; }

.feed-item {
  display:flex;
  gap:10px;
  padding:10px 12px;
  border-radius:12px;
  border:1px solid rgba(255,255,255,.05);
  background: rgba(18,25,38,.76);
  margin-bottom:8px;
}
.feed-dot  {
  width:9px;
  height:9px;
  border-radius:999px;
  background: var(--green);
  box-shadow:0 0 10px var(--green);
  margin-top:7px;
  flex:0 0 9px;
}
.feed-time { color:#8fa2c4; font-size:.73rem; }
.feed-text { color:#e6efff; font-size:.83rem; line-height:1.45; }

.status-item {
  display:flex;
  gap:10px;
  align-items:flex-start;
  padding:10px 12px;
  border-radius:16px;
  border:1px solid rgba(255,255,255,.06);
  background: linear-gradient(180deg, rgba(28,36,51,.88), rgba(20,27,39,.92));
  margin-bottom:8px;
}
.status-title { font-size:.85rem; font-weight:800; color:#f5f9ff; margin-bottom:3px; }
.status-text  { font-size:.77rem; color:#93a6c8; line-height:1.45; }
.dot { display:inline-block; width:10px; height:10px; border-radius:999px; margin-top:5px; flex:0 0 10px; }
.dot-pending { background:#7c8aa6; }
.dot-running { background:#55e6ff; box-shadow:0 0 12px #55e6ff; }
.dot-done    { background:#4fffb0; box-shadow:0 0 12px #4fffb0; }
.dot-error   { background:#ff6b7d; box-shadow:0 0 12px #ff6b7d; }

.tool-card {
  padding:14px;
  border-radius:16px;
  border:1px solid rgba(255,255,255,.06);
  background: linear-gradient(180deg, rgba(28,36,51,.88), rgba(20,27,39,.92));
  margin-bottom:8px;
}
.tool-head  { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.tool-title { font-size:.86rem; font-weight:800; color:#f5f9ff; }
.tool-badge {
  font-size:.72rem;
  color:#bcecff;
  border:1px solid rgba(85,230,255,.2);
  background:rgba(85,230,255,.08);
  border-radius:999px;
  padding:4px 8px;
}
.tool-text {
  font-size:.78rem;
  line-height:1.5;
  color:#93a6c8;
  white-space:pre-wrap;
  word-break:break-word;
}

.rx-pill {
  display:inline-block;
  border:1px solid rgba(255,255,255,.08);
  background:rgba(17,26,45,.9);
  border-radius:999px;
  padding:5px 12px;
  font-size:.75rem;
  color:#dce7f7;
  margin:3px;
}

.cal-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:8px; }
.cal-day-name { text-align:center; font-size:.72rem; color:#93a6c8; font-weight:700; padding-bottom:6px; }
.cal-cell {
  min-height:70px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,.05);
  background:rgba(12,18,32,.6);
  padding:8px;
}
.cal-cell.dim   { opacity:.3; }
.cal-cell.today { border-color:rgba(85,230,255,.35); box-shadow:0 0 14px rgba(85,230,255,.1); }
.cal-date { font-size:.76rem; font-weight:800; color:#dce7f7; margin-bottom:4px; }
.cal-pill {
  border-radius:999px;
  padding:3px 7px;
  font-size:.67rem;
  font-weight:700;
  background:rgba(93,133,255,.18);
  color:#ddecff;
  border:1px solid rgba(93,133,255,.16);
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  display:block;
  margin-top:3px;
}

.kanban-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.kan-col {
  border-radius:16px;
  border:1px solid rgba(255,255,255,.05);
  background:rgba(13,19,33,.72);
  padding:12px;
  min-height:220px;
}
.kan-head { display:flex; justify-content:space-between; margin-bottom:10px; font-size:.82rem; font-weight:800; color:#f5f9ff; }
.task-card {
  border-radius:12px;
  border:1px solid rgba(255,255,255,.05);
  background:rgba(18,27,45,.92);
  padding:10px;
  margin-bottom:8px;
}
.task-title { font-size:.8rem; font-weight:800; color:#f5f9ff; margin-bottom:3px; }
.task-sub   { font-size:.72rem; color:#93a6c8; line-height:1.4; }

.chat-msg-user {
  background: linear-gradient(135deg,#5d85ff,#7ca4ff);
  color: white;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: .86rem;
  line-height: 1.5;
  margin-bottom: 8px;
  max-width: 90%;
  margin-left: auto;
  text-align: right;
}
.chat-msg-bot {
  background: rgba(17,26,45,.95);
  border: 1px solid rgba(255,255,255,.07);
  color: #dbe7f7;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: .86rem;
  line-height: 1.5;
  margin-bottom: 8px;
}
.chat-msg-sys {
  background: rgba(85,230,255,.07);
  border: 1px solid rgba(85,230,255,.14);
  color: #9ecfdf;
  border-radius: 14px;
  padding: 8px 12px;
  font-size: .78rem;
  font-style: italic;
  margin-bottom: 8px;
}

.bar-row {
  display:grid;
  grid-template-columns:130px 1fr 40px;
  gap:10px;
  align-items:center;
  margin-bottom:10px;
}
.bar-label { font-size:.84rem; color:#d9e6f7; }
.bar-track {
  height:14px;
  border-radius:999px;
  background: rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.05);
  overflow:hidden;
}
.bar-fill  {
  height:100%;
  border-radius:999px;
  box-shadow: 0 0 16px currentColor;
}
.bar-value { text-align:right; font-weight:800; font-size:.8rem; color:#f5f9ff; }

.side-label {
  color:#8fa3c7;
  font-size:.72rem;
  font-weight:800;
  text-transform:uppercase;
  letter-spacing:.15em;
  padding:0 4px;
  margin-top:8px;
}

.product-card {
  border-radius:16px;
  border:1px solid rgba(255,255,255,.06);
  background: linear-gradient(180deg, rgba(28,36,51,.88), rgba(20,27,39,.92));
  padding:16px;
  margin-bottom:12px;
}
.mini-stat {
  border-radius:12px;
  border:1px solid rgba(255,255,255,.05);
  background:#111a2d;
  padding:10px;
  text-align:center;
}
.mini-stat span   { display:block; color:#93a6c8; font-size:.72rem; margin-bottom:5px; }
.mini-stat strong { font-size:.92rem; font-weight:800; color:#f5f9ff; }

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
  right: 20px !important;
  bottom: 120px !important;
  z-index: 9999 !important;
  width: 390px !important;
  max-width: calc(100vw - 24px) !important;
  background: #08111d !important;
  border-radius: 22px !important;
  border: 1px solid rgba(93,133,255,.22) !important;
  box-shadow: 0 24px 64px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.04) !important;
  padding: 0 !important;
  overflow: hidden !important;
}
div.st-key-rx_chat_panel > div,
div.st-key-rx_chat_panel [data-testid="stVerticalBlock"],
div.st-key-rx_chat_panel [data-testid="column"] {
  background: #08111d !important;
  box-shadow: none !important;
  border: none !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}
.rx-chat-shell {
  width: 100%;
  border-radius: 22px;
  overflow: hidden;
  background: #08111d;
  border: none;
  box-shadow: none;
}
.rx-chat-header {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:14px 16px;
  border-bottom:1px solid rgba(255,255,255,.06);
  background: rgba(13,22,40,.96);
}
.rx-chat-header-left {
  display:flex;
  align-items:center;
  gap:10px;
}
.rx-chat-header-dot {
  width:8px;
  height:8px;
  border-radius:999px;
  background:#55e6ff;
  box-shadow:0 0 8px #55e6ff;
}
.rx-chat-header-title {
  font-weight:800;
  font-size:.9rem;
  color:#f5f9ff;
}
.rx-chat-messages {
  max-height: 220px;
  overflow-y: auto;
  padding: 12px 12px 4px 12px;
  background: rgba(8,14,25,.98);
}
.rx-chat-form {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,.06);
  background: rgba(9,16,28,.98);
}
.rx-chat-sample-note {
  font-size:.72rem;
  color:#7f90b1;
  margin-bottom:6px;
  font-weight:700;
  text-transform:uppercase;
  letter-spacing:.10em;
}
div.st-key-rx_chat_close button {
  width: 30px !important;
  height: 30px !important;
  min-height: 30px !important;
  border-radius: 8px !important;
  padding: 0 !important;
  font-size: 18px !important;
  background: rgba(255,255,255,.04) !important;
  border: 1px solid rgba(255,255,255,.10) !important;
}
div.st-key-rx_chat_close button:hover {
  background: rgba(255,107,125,.12) !important;
  border-color: rgba(255,107,125,.2) !important;
  color: #ff6b7d !important;
}
div.st-key-rx_chat_panel .stSelectbox,
div.st-key-rx_chat_panel .stTextArea,
div.st-key-rx_chat_panel .stButton {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}
div.st-key-rx_chat_panel .stTextArea textarea {
  min-height: 110px !important;
}
div.st-key-rx_chat_panel .stSelectbox > div > div,
div.st-key-rx_chat_panel .stTextArea textarea {
  background: #0c1526 !important;
}
div.st-key-rx_chat_panel .stButton button {
  height: 46px !important;
  min-height: 46px !important;
}

@media (max-width: 900px) {
  div.st-key-rx_chat_panel {
    width: calc(100vw - 24px) !important;
    right: 12px !important;
    bottom: 108px !important;
  }
  div.st-key-rx_chat_fab {
    right: 12px !important;
    bottom: 18px !important;
  }
}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────────

def esc(x):
    return html.escape("" if x is None else str(x))

def now_label():
    return datetime.now().strftime("%B %d, %Y  %H:%M:%S")

def safe_json(value, fallback=None):
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except Exception:
        return fallback if fallback is not None else {}

def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        if "application/json" in r.headers.get("content-type", ""):
            return True, r.json()
        return True, {"text": r.text}
    except Exception as e:
        return False, {"error": str(e)}

def api_post(path, payload=None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload or {}, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        if "application/json" in r.headers.get("content-type", ""):
            return True, r.json()
        return True, {"text": r.text}
    except Exception as e:
        return False, {"error": str(e)}

def pull_list(data, *keys):
    for k in keys:
        if isinstance(data, dict) and isinstance(data.get(k), list):
            return data.get(k)
    return []

@st.cache_data(ttl=2)
def fetch_all_data():
    ok_c, c_data = api_get("/complaints")
    ok_p, p_data = api_get("/products")
    ok_d, d_data = api_get("/dashboard")
    ok_h, h_data = api_get("/health")

    complaints = []
    pending = []
    products = []
    summary = {}
    api_ok = ok_h or ok_c or ok_p or ok_d

    if ok_c:
        if isinstance(c_data, list):
            complaints = c_data
        elif isinstance(c_data, dict):
            complaints = pull_list(c_data, "complaints", "items", "data")
            pending = pull_list(c_data, "pending", "pending_cases", "manufacturer_pending")

    if ok_p:
        if isinstance(p_data, list):
            products = p_data
        elif isinstance(p_data, dict):
            products = pull_list(p_data, "products", "items", "data", "product_stats")

    if ok_d and isinstance(d_data, dict):
        summary = d_data.get("data", d_data)

    return {
        "api_ok": api_ok,
        "health": h_data if ok_h else {},
        "complaints": complaints,
        "pending": pending,
        "products": products,
        "summary": summary,
    }

def status_color(status):
    status = str(status or "").lower()
    if status in {"running", "active", "in_progress"}:
        return "running"
    if status in {"done", "complete", "completed", "ok", "healthy", "connected"}:
        return "done"
    if status in {"error", "failed", "down"}:
        return "error"
    return "pending"

def append_chat(kind, text):
    st.session_state.chat_messages.append({
        "kind": kind,
        "text": text,
        "ts": datetime.now().strftime("%H:%M")
    })

def push_trace(text, status="OK"):
    st.session_state.trace_lines.insert(0, {
        "text": text,
        "status": status,
        "ts": datetime.now().strftime("%H:%M:%S")
    })
    st.session_state.trace_lines = st.session_state.trace_lines[:12]

def push_activity(text):
    st.session_state.activity_feed.insert(0, {
        "text": text,
        "ts": datetime.now().strftime("%H:%M:%S")
    })
    st.session_state.activity_feed = st.session_state.activity_feed[:14]

def set_status(name, state, desc):
    st.session_state.system_status[name] = {"state": state, "desc": desc}

def set_tool(name, content):
    st.session_state.tool_panels[name] = content

def infer_counts(complaints, summary, pending):
    total_c = len(complaints)

    active = sum(
        1 for c in complaints
        if not c.get("loop_closed_at")
        and str(c.get("status", "")).lower() not in {"closed", "resolved", "complete", "completed"}
    )
    resolved = sum(
        1 for c in complaints
        if c.get("loop_closed_at")
        or c.get("resolution")
        or str(c.get("status", "")).lower() in {"closed", "resolved", "complete", "completed"}
    )
    escalated = sum(
        1 for c in complaints
        if c.get("escalated")
        or c.get("manufacturer_contacted")
        or str(c.get("decision", "")).lower() == "escalate"
    )

    overdue = 0
    now_dt = datetime.now()
    for c in complaints:
        due = c.get("eta") or c.get("sla_due") or c.get("due_date")
        if not due:
            continue
        try:
            due_dt = datetime.fromisoformat(str(due).replace("Z", "+00:00").replace("+00:00", ""))
            closed = c.get("loop_closed_at") or c.get("resolved_at")
            if due_dt < now_dt and not closed:
                overdue += 1
        except Exception:
            pass

    if summary.get("total_complaints") is not None:
        total_c = summary.get("total_complaints", total_c)
    if summary.get("active_cases") is not None:
        active = summary.get("active_cases", active)
    if summary.get("resolved") is not None:
        resolved = summary.get("resolved", resolved)
    if summary.get("escalated") is not None:
        escalated = summary.get("escalated", escalated)
    if summary.get("sla_overdue") is not None:
        overdue = summary.get("sla_overdue", overdue)

    manufacturer_cases = len(pending) or summary.get("manufacturer_contacted", 0)
    return total_c, active, resolved, escalated, overdue, manufacturer_cases

def compute_issue_breakdown(complaints):
    out = {}
    for c in complaints:
        key = c.get("issue_type") or c.get("category") or c.get("complaint_type") or c.get("type") or "General"
        out[key] = out.get(key, 0) + 1
    if not out:
        out = {"General": 1}
    return dict(sorted(out.items(), key=lambda x: x[1], reverse=True)[:6])

def compute_resolution_breakdown(complaints):
    out = {}
    for c in complaints:
        key = c.get("resolution") or c.get("decision") or c.get("outcome") or c.get("status") or "Pending"
        key = str(key).replace("_", " ").title()
        out[key] = out.get(key, 0) + 1
    if not out:
        out = {"Pending": 1}
    return dict(sorted(out.items(), key=lambda x: x[1], reverse=True)[:6])

def build_calendar_items(complaints):
    items = {}
    for c in complaints:
        raw = c.get("eta") or c.get("follow_up_date") or c.get("due_date")
        label = c.get("product_name") or c.get("product") or c.get("order_id") or "Case"
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00").replace("+00:00", ""))
            d = dt.date().isoformat()
            items.setdefault(d, []).append(label)
        except Exception:
            continue
    return items

def build_kanban(complaints):
    cols = {"New": [], "Analyzing": [], "Manufacturer": [], "Resolved": []}
    for c in complaints[:24]:
        status = str(c.get("status", "")).lower()
        title = c.get("product_name") or c.get("product") or c.get("order_id") or "Case"
        sub = c.get("issue_type") or c.get("category") or c.get("complaint") or c.get("summary") or "Complaint case"
        item = {"title": title, "sub": str(sub)[:80]}

        if status in {"resolved", "closed", "complete", "completed"} or c.get("loop_closed_at"):
            cols["Resolved"].append(item)
        elif c.get("manufacturer_contacted") or c.get("escalated") or status == "escalate":
            cols["Manufacturer"].append(item)
        elif status in {"analyzing", "analysis", "processing", "investigating", "in_progress"}:
            cols["Analyzing"].append(item)
        else:
            cols["New"].append(item)
    return cols

def dedupe_cases(cases):
    seen = set()
    out = []
    for c in cases:
        key = c.get("complaint_id") or (
            c.get("order_id"),
            c.get("product_name") or c.get("product"),
            c.get("issue_type") or c.get("category"),
            c.get("status") or c.get("resolution"),
            c.get("complaint") or c.get("summary"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out

def latest_case_data():
    latest_data = fetch_all_data()
    latest_complaints = dedupe_cases(latest_data.get("complaints", []))
    latest_products = latest_data.get("products", [])

    latest_case = latest_complaints[0] if latest_complaints else {}
    latest_product_stats = {}

    product_name = latest_case.get("product_name") or latest_case.get("product")
    if product_name and latest_products:
        for p in latest_products:
            p_name = p.get("name") or p.get("product_name")
            if p_name == product_name:
                latest_product_stats = p
                break

    return latest_case, latest_product_stats

def build_notes_text(case: dict) -> str:
    if not case:
        return "No case notes yet."

    product_name = case.get("product_name") or case.get("product") or "Unknown"
    order_id = case.get("order_id") or "Not provided"
    issue_type = case.get("issue_type") or case.get("category") or "other"
    summary = case.get("complaint_summary") or case.get("summary") or case.get("complaint") or "No summary available."
    resolution = case.get("resolution") or case.get("decision") or "Pending"
    reason = case.get("decision_reason") or "No decision reason available."
    priority = case.get("priority") or case.get("urgency_level") or "medium"
    eta = case.get("estimated_resolution_days") or case.get("eta") or "N/A"

    return (
        f"Product: {product_name}\n"
        f"Order ID: {order_id}\n"
        f"Issue Type: {issue_type}\n"
        f"Priority: {priority}\n"
        f"Resolution: {resolution}\n"
        f"ETA: {eta}\n"
        f"Summary: {summary}\n"
        f"Reason: {reason}"
    )

def build_tracker_text(result: dict, product_name: str) -> str:
    if not result:
        return f"Tracker ran for {product_name}, but no details were returned."
    parsed = safe_json(result, {})
    status = parsed.get("status") or parsed.get("result", {}).get("status") or "completed"
    return f"Tracker status: {status}\nProduct: {product_name}"

def build_manufacturer_text(case: dict, product_stats: dict) -> str:
    if not case:
        return "No manufacturer activity yet."

    product_name = case.get("product_name") or case.get("product") or "Unknown"
    manufacturer_contacted = case.get("manufacturer_contacted") or product_stats.get("manufacturer_contacted", False)
    manufacturer_resolved = case.get("manufacturer_resolved") or product_stats.get("manufacturer_resolved", False)

    return (
        f"Product: {product_name}\n"
        f"Manufacturer Contacted: {'Yes' if manufacturer_contacted else 'No'}\n"
        f"Manufacturer Resolved: {'Yes' if manufacturer_resolved else 'No'}"
    )

def render_trace_html():
    rows = st.session_state.trace_lines or [{"text": "System initialized.", "status": "OK"}]
    return "".join(
        f'<div class="trace-line"><div class="trace-left">{esc(r.get("text",""))}</div><div class="trace-right">{esc(r.get("status","OK"))}</div></div>'
        for r in rows
    )

def render_activity_html():
    rows = st.session_state.activity_feed or [{"text": "Awaiting events.", "ts": datetime.now().strftime("%H:%M:%S")}]
    out = []
    for row in rows:
        out.append(
            f'''
            <div class="feed-item">
              <div class="feed-dot"></div>
              <div>
                <div class="feed-time">{esc(row.get("ts",""))}</div>
                <div class="feed-text">{esc(row.get("text",""))}</div>
              </div>
            </div>
            '''
        )
    return "".join(out)

def render_status_html():
    items = st.session_state.system_status
    order = ["listener", "analyst", "decision", "manufacturer", "tracker", "database"]
    names = {
        "listener": "Listener Agent",
        "analyst": "Analyst Agent",
        "decision": "Decision Agent",
        "manufacturer": "Manufacturer Agent",
        "tracker": "Tracker Agent",
        "database": "Database Agent",
    }
    out = []
    for key in order:
        data = items.get(key, {"state": "pending", "desc": "Waiting..."})
        cls = status_color(data.get("state"))
        out.append(
            f'''
            <div class="status-item">
              <span class="dot dot-{cls}"></span>
              <div>
                <div class="status-title">{esc(names.get(key, key.title()))}</div>
                <div class="status-text">{esc(data.get("desc",""))}</div>
              </div>
            </div>
            '''
        )
    return "".join(out)

def render_tools_html():
    panels = st.session_state.tool_panels
    labels = {
        "notes": "Notes",
        "tasks": "Tasks",
        "manufacturer": "Manufacturer",
        "tracker": "Tracker",
        "calendar": "Calendar",
    }
    badges = {
        "notes": "Memory",
        "tasks": "Board",
        "manufacturer": "Escalation",
        "tracker": "Follow-up",
        "calendar": "Schedule",
    }
    out = []
    for key in ["notes", "tasks", "manufacturer", "tracker", "calendar"]:
        out.append(
            f'''
            <div class="tool-card">
              <div class="tool-head">
                <div class="tool-title">{esc(labels[key])}</div>
                <div class="tool-badge">{esc(badges[key])}</div>
              </div>
              <div class="tool-text">{esc(panels.get(key, "No output yet."))}</div>
            </div>
            '''
        )
    return "".join(out)

def render_chat_html():
    rows = st.session_state.chat_messages or [{"kind": "bot", "text": "Hi, I’m ResolveX Assistant. Tell me what happened and I’ll help you resolve it."}]
    out = []
    for row in rows[-12:]:
        kind = row.get("kind", "bot")
        klass = "chat-msg-bot"
        if kind == "user":
            klass = "chat-msg-user"
        elif kind == "sys":
            klass = "chat-msg-sys"
        out.append(f'<div class="{klass}">{esc(row.get("text",""))}</div>')
    return "".join(out)

def render_bars_html(data):
    vals = list(data.values()) or [1]
    max_v = max(vals) if vals else 1
    fills = [
        "linear-gradient(90deg,#5d85ff,#7ca4ff)",
        "linear-gradient(90deg,#55e6ff,#80f1ff)",
        "linear-gradient(90deg,#4fffb0,#7effc9)",
        "linear-gradient(90deg,#ca6dff,#e19bff)",
        "linear-gradient(90deg,#ff9f66,#ffbe8f)",
        "linear-gradient(90deg,#ffd166,#ffe39a)",
    ]
    rows = []
    for i, (label, value) in enumerate(data.items()):
        width = max(8, int((value / max_v) * 100)) if max_v else 0
        rows.append(
            f'''
            <div class="bar-row">
              <div class="bar-label">{esc(label)}</div>
              <div class="bar-track"><div class="bar-fill" style="width:{width}%;background:{fills[i % len(fills)]};"></div></div>
              <div class="bar-value">{esc(value)}</div>
            </div>
            '''
        )
    return "".join(rows)

def render_donut_html(data):
    total = sum(data.values()) or 1
    radius = 72
    stroke = 18
    circumference = 2 * math.pi * radius
    colors = ["#5d85ff", "#55e6ff", "#4fffb0", "#ca6dff", "#ff9f66", "#ffd166"]
    acc = 0.0
    segs = []
    legend = []

    for i, (label, value) in enumerate(data.items()):
        frac = value / total
        dash = frac * circumference
        gap = circumference - dash
        color = colors[i % len(colors)]
        offset = -acc * circumference
        acc += frac
        segs.append(
            f'<circle cx="100" cy="100" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-dasharray="{dash} {gap}" stroke-dashoffset="{offset}" transform="rotate(-90 100 100)"></circle>'
        )
        legend.append(
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin:8px 0;">'
            f'<div style="display:flex;align-items:center;gap:8px;color:#dce7f7;font-size:.8rem;">'
            f'<span style="width:10px;height:10px;border-radius:999px;background:{color};display:inline-block;"></span>{esc(label)}</div>'
            f'<div style="color:#f5f9ff;font-weight:800;font-size:.8rem;">{value}</div></div>'
        )

    return f'''
    <div style="display:grid;grid-template-columns:220px 1fr;gap:10px;align-items:center;">
      <div style="display:flex;justify-content:center;">
        <svg width="220" height="220" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="{radius}" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="{stroke}"></circle>
          {''.join(segs)}
          <text x="100" y="95" text-anchor="middle" fill="#93a6c8" font-size="12" font-weight="700">Total</text>
          <text x="100" y="118" text-anchor="middle" fill="#f5f9ff" font-size="24" font-weight="800">{total}</text>
        </svg>
      </div>
      <div>{''.join(legend)}</div>
    </div>
    '''

def render_calendar_html(items):
    now = datetime.now()
    y, m = now.year, now.month
    cal = cal_mod.Calendar(firstweekday=0)
    month_days = list(cal.monthdatescalendar(y, m))
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    head = "".join([f'<div class="cal-day-name">{d}</div>' for d in day_names])
    cells = []
    for week in month_days:
        for d in week:
            cls = "cal-cell"
            if d.month != m:
                cls += " dim"
            if d == now.date():
                cls += " today"
            key = d.isoformat()
            pills = "".join(f'<span class="cal-pill">{esc(x)[:20]}</span>' for x in items.get(key, [])[:3])
            cells.append(f'<div class="{cls}"><div class="cal-date">{d.day}</div>{pills}</div>')
    return f'<div class="cal-grid">{head}{"".join(cells)}</div>'

def render_kanban_html(columns):
    html_parts = ['<div class="kanban-grid">']
    for col_name, items in columns.items():
        html_parts.append(
            f'<div class="kan-col"><div class="kan-head"><span>{esc(col_name)}</span><span>{len(items)}</span></div>'
        )

        if not items:
            html_parts.append('<div class="task-card"><div class="task-sub">No items</div></div>')
        else:
            for item in items:
                title = esc(item.get("title", "Case"))
                sub = esc(item.get("sub", ""))
                html_parts.append(
                    f'<div class="task-card"><div class="task-title">{title}</div><div class="task-sub">{sub}</div></div>'
                )
        html_parts.append('</div>')

    html_parts.append('</div>')
    return "".join(html_parts)

def reset_session():
    st.session_state.chat_messages = [
        {"kind": "bot", "text": "Hi, I’m ResolveX Assistant. Tell me what happened and I’ll help you resolve it."}
    ]
    st.session_state.trace_lines = [{"text": "System reset.", "status": "OK"}]
    st.session_state.activity_feed = [{"text": "Dashboard reset.", "ts": datetime.now().strftime("%H:%M:%S")}]
    st.session_state.last_product = None
    st.session_state.complaint_text = ""
    st.session_state.sample_choice = "Custom..."
    st.session_state.tool_panels = {
        "notes": "No case notes yet.",
        "tasks": "No tasks yet.",
        "manufacturer": "No manufacturer activity yet.",
        "tracker": "No tracker output yet.",
        "calendar": "No calendar items yet.",
    }
    st.session_state.system_status = {
        "listener": {"state": "pending", "desc": "Awaiting complaint input."},
        "analyst": {"state": "pending", "desc": "Awaiting complaint analysis."},
        "decision": {"state": "pending", "desc": "Awaiting routing decision."},
        "manufacturer": {"state": "pending", "desc": "No manufacturer escalation yet."},
        "tracker": {"state": "pending", "desc": "No follow-up triggered yet."},
        "database": {"state": "pending", "desc": "Waiting to log case data."},
    }

    for key in ["rx_chat_textarea", "rx_chat_sample_select"]:
        if key in st.session_state:
            del st.session_state[key]

def do_submit_complaint(text):
    append_chat("user", text)
    append_chat("sys", "Submitting complaint...")
    push_trace("[COMPLAINT_ANALYSIS] Analyzing text sentiment...", "RUN")
    push_activity("Complaint submitted")
    set_status("listener", "running", "Understanding complaint...")

    ok, res = api_post("/complaint", {"complaint": text})

    if not ok:
        set_status("listener", "error", "Failed to connect to API.")
        append_chat("bot", f"API error: {res.get('error', 'Unknown error')}")
        push_trace("[COMPLAINT_ANALYSIS] Complaint submission failed.", "ERR")
        return

    result_blob = safe_json(res, {})
    customer_response = result_blob.get("customer_response", {}) or {}

    set_status("listener", "done", "Complaint parsed successfully.")
    set_status("analyst", "done", "Issue severity and eligibility evaluated.")
    set_status("decision", "done", "Decision generated.")
    set_status("database", "done", "Complaint stored successfully.")

    st.cache_data.clear()
    latest_case, latest_product_stats = latest_case_data()

    prod = latest_case.get("product_name") or latest_case.get("product") or latest_case.get("order_id")
    if prod:
        st.session_state.last_product = prod

    resolution_text = (
        customer_response.get("customer_message")
        or customer_response.get("resolution")
        or customer_response.get("acknowledgement")
        or result_blob.get("message")
        or "Your complaint has been reviewed and recorded."
    )

    append_chat("bot", f"{resolution_text}\n\nThanks for reporting this — your case has been logged and is being handled.")

    if latest_case.get("manufacturer_contacted") or latest_product_stats.get("manufacturer_contacted", False):
        set_status("manufacturer", "running", "Escalation sent to manufacturer.")
    else:
        set_status("manufacturer", "pending", "No manufacturer escalation required yet.")

    set_tool("notes", build_notes_text(latest_case))
    set_tool("manufacturer", build_manufacturer_text(latest_case, latest_product_stats))
    set_tool("tasks", "Task board refreshed from latest complaint data.")

    push_trace("[RESOLUTION_AGENT] Proposed resolution successfully.", "OK")
    push_activity("Case updated by backend")

    if latest_case.get("is_resolved") or latest_case.get("resolution"):
        append_chat("sys", "Case recorded successfully.")

def run_tracker_action():
    prod = st.session_state.last_product

    if not prod:
        latest_case, _ = latest_case_data()
        prod = latest_case.get("product_name") or latest_case.get("product") or latest_case.get("order_id")
        if prod:
            st.session_state.last_product = prod

    if not prod:
        append_chat("sys", "No product available yet. Submit a complaint first.")
        return

    push_trace(f"[TRACKER_AGENT] Running tracker for {prod}...", "RUN")
    push_activity(f"Tracker started for {prod}")
    set_status("tracker", "running", f"Running tracker for {prod}...")

    ok, res = api_post("/tracker/run", {"product_name": prod})

    if ok and safe_json(res, {}).get("success", True):
        set_status("tracker", "done", "Tracker executed successfully.")
        set_tool("tracker", build_tracker_text(res, prod))
        append_chat("sys", f"Tracker completed for {prod}.")
        push_trace(f"[TRACKER_AGENT] Tracker completed for {prod}.", "OK")
    else:
        set_status("tracker", "error", "Tracker failed.")
        append_chat("sys", f"Tracker failed for {prod}.")
        push_trace(f"[TRACKER_AGENT] Tracker failed for {prod}.", "ERR")

    st.cache_data.clear()

def run_learning_action():
    append_chat("sys", "Running learning agent...")
    push_trace("[LEARNING_AGENT] Analyzing patterns...", "RUN")
    push_activity("Learning agent started")

    ok, res = api_post("/learning/run", {})

    if ok and safe_json(res, {}).get("success", True):
        append_chat("sys", "Learning agent finished successfully.")
        push_trace("[LEARNING_AGENT] Learning completed.", "OK")
    else:
        parsed = safe_json(res, {})
        append_chat("sys", f"Learning endpoint unavailable or failed: {parsed.get('error', 'Unknown error')}")
        push_trace("[LEARNING_AGENT] Endpoint unavailable.", "ERR")

def on_sample_change():
    selected_now = st.session_state.rx_chat_sample_select
    st.session_state.sample_choice = selected_now
    if selected_now == "Custom...":
        st.session_state.rx_chat_textarea = ""
        st.session_state.complaint_text = ""
    else:
        st.session_state.rx_chat_textarea = selected_now
        st.session_state.complaint_text = selected_now

# ── SESSION STATE ───────────────────────────────────────────────────────────

if "chat_messages" not in st.session_state:
    reset_session()

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "rx_chat_textarea" not in st.session_state:
    st.session_state.rx_chat_textarea = st.session_state.get("complaint_text", "")

# ── LOAD DATA ────────────────────────────────────────────────────────────────

data = fetch_all_data()
api_ok = data["api_ok"]
complaints = dedupe_cases(data["complaints"])
pending = dedupe_cases(data["pending"])
products = dedupe_cases(data["products"])
summary = data["summary"]

total_c, active_cases, resolved_cases, escalated, overdue, manufacturer_cases = infer_counts(
    complaints, summary, pending
)
issue_types = compute_issue_breakdown(complaints)
resolution = compute_resolution_breakdown(complaints)
calendar_items = build_calendar_items(complaints)
kanban_cols = build_kanban(complaints)

st.session_state.tool_panels["calendar"] = f"{len(calendar_items)} scheduled day(s) with follow-ups or ETA items."

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
    st.markdown(
        f'<div style="font-weight:700;font-size:.85rem;color:{color_api};margin-bottom:4px;">● {label_api}</div>',
        unsafe_allow_html=True
    )
    st.caption(f"→ {API_BASE}")

    st.markdown('<div class="side-label" style="margin-top:14px;">Navigation</div>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["Overview", "Operations", "Complaints", "Products"],
        label_visibility="collapsed",
        key="sidebar_nav"
    )

    st.markdown('<hr style="margin:14px 0;">', unsafe_allow_html=True)

    if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_btn"):
        st.cache_data.clear()
        push_activity("Dashboard refreshed")
        st.rerun()

    if st.button("🧹 Reset Session", use_container_width=True, key="reset_btn_sidebar"):
        reset_session()
        st.cache_data.clear()
        st.rerun()

    st.markdown("""
    <div style="margin-top:8px;padding:12px;border-radius:16px;
                border:1px solid rgba(255,255,255,.06);
                background:linear-gradient(180deg, rgba(28,36,51,.88), rgba(20,27,39,.92));
                font-size:.78rem;color:#93a6c8;line-height:1.6;">
      Multi-agent complaint understanding, decisioning, escalation, and follow-up activity in one command center.
    </div>
    """, unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="margin-bottom:10px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <div style="width:10px;height:10px;border-radius:999px;background:#9dff8a;box-shadow:0 0 12px #9dff8a;"></div>
    <div style="font-size:.78rem;font-weight:800;letter-spacing:.16em;color:#8fa3c7;text-transform:uppercase;">
      ResolveX Command Center
    </div>
  </div>

  <h1 style="margin:0;font-size:2.1rem;font-weight:800;letter-spacing:-.05em;color:#f5f9ff;line-height:1.1;">
    Autonomous Customer Resolution Dashboard
  </h1>

  <p style="margin:10px 0 0;color:#c6d6ee;line-height:1.65;font-size:.95rem;max-width:980px;">
    Monitor complaints, resolution decisions, escalations, product issues, and live follow-up activity in one place.
  </p>

  <div style="margin-top:12px;color:#8da2c6;font-size:.82rem;font-weight:700;">
    Updated live • {now_label()}
  </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ── FLOATING CHAT BUTTON ─────────────────────────────────────────────────────

fab_wrap = st.container(key="rx_chat_fab")
with fab_wrap:
    if st.button("", key="rx_chat_fab_btn"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

# ── FLOATING CHAT PANEL ──────────────────────────────────────────────────────

if st.session_state.chat_open:
    panel = st.container(key="rx_chat_panel")
    with panel:
        header_cols = st.columns([10, 1])
        with header_cols[0]:
            st.markdown("""
            <div class="rx-chat-shell">
              <div class="rx-chat-header">
                <div class="rx-chat-header-left">
                  <div class="rx-chat-header-dot"></div>
                  <div class="rx-chat-header-title">ResolveX Assistant</div>
                </div>
              </div>
            """, unsafe_allow_html=True)

        with header_cols[1]:
            close_wrap = st.container(key="rx_chat_close")
            with close_wrap:
                if st.button("✕", key="rx_chat_close_btn"):
                    st.session_state.chat_open = False
                    st.rerun()

        st.markdown('<div class="rx-chat-messages">', unsafe_allow_html=True)
        st.markdown(render_chat_html(), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="rx-chat-form">', unsafe_allow_html=True)
        st.markdown('<div class="rx-chat-sample-note">Quick samples</div>', unsafe_allow_html=True)

        samples = [
            "Custom...",
            "My Voltix Charger overheats after five minutes and stopped working. Order ORD001.",
            "I received the wrong AeroBuds Pro color and the box was already damaged. Order ORD003.",
            "The Nova Blender has a broken motor and makes a burning smell after two uses. Order ORD002.",
            "My headphones stopped charging after only 2 weeks. Very frustrated. Order ORD003.",
        ]

        sample_index = samples.index(st.session_state.sample_choice) if st.session_state.sample_choice in samples else 0

        st.selectbox(
            "Sample complaint",
            samples,
            index=sample_index,
            label_visibility="collapsed",
            key="rx_chat_sample_select",
            on_change=on_sample_change
        )

        complaint_input = st.text_area(
            "Complaint",
            height=110,
            placeholder="Describe your issue here...",
            label_visibility="collapsed",
            key="rx_chat_textarea"
        )

        st.session_state.complaint_text = complaint_input

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            if st.button("Send", use_container_width=True, key="rx_chat_send_btn"):
                text_to_send = st.session_state.rx_chat_textarea.strip()
                if text_to_send and len(text_to_send) >= 10:
                    st.session_state.complaint_text = text_to_send
                    do_submit_complaint(text_to_send)
                    st.session_state.chat_open = True
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Enter at least 10 characters.")

        with row1_col2:
            if st.button("Reset", use_container_width=True, key="rx_chat_reset_btn"):
                reset_session()
                st.session_state.chat_open = True
                st.rerun()

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            if st.button("Tracker", use_container_width=True, key="rx_chat_tracker_btn"):
                run_tracker_action()
                st.session_state.chat_open = True
                st.rerun()

        with row2_col2:
            if st.button("Learning", use_container_width=True, key="rx_chat_learning_btn"):
                run_learning_action()
                st.session_state.chat_open = True
                st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

# ── PAGE: OVERVIEW ───────────────────────────────────────────────────────────

if page == "Overview":
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Complaints", total_c)
    c2.metric("Active Cases", active_cases)
    c3.metric("Resolved", resolved_cases)
    c4.metric("Escalated", escalated)
    c5.metric("Manufacturer Cases", manufacturer_cases)
    c6.metric("SLA Overdue", overdue)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(
            '<div class="rx-card glow-green"><div class="rx-card-title">AI Thought Trace</div><div class="rx-card-desc">Readable multi-agent workflow progression.</div>',
            unsafe_allow_html=True
        )
        st.markdown(render_trace_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown(
            '<div class="rx-card glow-blue"><div class="rx-card-title">Live Activity Feed</div><div class="rx-card-desc">Recent operational events and updates.</div>',
            unsafe_allow_html=True
        )
        st.markdown(render_activity_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col_l2, col_r2 = st.columns([1.2, 1])
    with col_l2:
        st.markdown(
            '<div class="rx-card"><div class="rx-card-title">Resolution Breakdown</div><div class="rx-card-desc">Outcome distribution across complaints.</div>',
            unsafe_allow_html=True
        )
        st.markdown(render_bars_html(resolution), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r2:
        st.markdown(
            '<div class="rx-card"><div class="rx-card-title">Issue Type Distribution</div><div class="rx-card-desc">Current complaint category mix.</div>',
            unsafe_allow_html=True
        )
        st.markdown(render_donut_html(issue_types), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ── PAGE: OPERATIONS ─────────────────────────────────────────────────────────

elif page == "Operations":
    col_l, col_r = st.columns([1, 1.1])

    with col_l:
        st.markdown(
            '<div class="rx-card"><div class="rx-card-title">System Status</div><div class="rx-card-desc">Real subsystem states during execution.</div>',
            unsafe_allow_html=True
        )
        st.markdown(render_status_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown(
            '<div class="rx-card"><div class="rx-card-title">Operational Panels</div><div class="rx-card-desc">Notes, tasks, calendar, manufacturer, and tracker output.</div>',
            unsafe_allow_html=True
        )
        st.markdown(render_tools_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="rx-card"><div class="rx-card-title">Monthly Calendar</div><div class="rx-card-desc">ETA and follow-up visibility for this month.</div>',
        unsafe_allow_html=True
    )
    st.markdown(render_calendar_html(calendar_items), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    task_board_html = render_kanban_html(kanban_cols)
    st.markdown(
        f'''
        <div class="rx-card">
          <div class="rx-card-title">Task Board</div>
          <div class="rx-card-desc">Kanban-style complaint flow across stages.</div>
          {task_board_html}
        </div>
        ''',
        unsafe_allow_html=True
    )

# ── PAGE: COMPLAINTS ─────────────────────────────────────────────────────────

elif page == "Complaints":
    st.markdown(
        '<div class="rx-card"><div class="rx-card-title">Complaint Cases</div><div class="rx-card-desc">Latest complaint data returned by the API.</div>',
        unsafe_allow_html=True
    )

    if complaints:
        deduped_rows = []
        seen = set()

        for c in complaints:
            key = (
                c.get("order_id") or "Not provided",
                c.get("product_name") or c.get("product") or "",
                c.get("issue_type") or c.get("category") or "",
                c.get("status") or c.get("resolution") or "",
            )

            if key in seen:
                continue
            seen.add(key)

            deduped_rows.append({
                "Order ID": c.get("order_id") or "Not provided",
                "Product": c.get("product_name") or c.get("product"),
                "Issue Type": c.get("issue_type") or c.get("category"),
                "Status": c.get("status") or c.get("resolution"),
                "Decision": c.get("decision"),
                "Escalated": c.get("escalated") or c.get("manufacturer_contacted"),
                "ETA": c.get("eta") or c.get("follow_up_date") or c.get("due_date"),
                "Summary": c.get("summary") or c.get("complaint"),
            })

        st.dataframe(pd.DataFrame(deduped_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No complaints returned yet.")

    st.markdown("</div>", unsafe_allow_html=True)


# ── PAGE: PRODUCTS ───────────────────────────────────────────────────────────

elif page == "Products":
    st.markdown(
        '<div class="rx-card"><div class="rx-card-title">Products</div><div class="rx-card-desc">Product catalog or complaint-linked products returned by the API.</div>',
        unsafe_allow_html=True
    )

    complaint_counts = {}
    for c in complaints:
        pname = c.get("product_name") or c.get("product")
        if pname:
            complaint_counts[pname] = complaint_counts.get(pname, 0) + 1

    if not products:
        st.info("No products returned from the backend yet.")
    else:
        seen_products = set()

        for product in products:
            name = product.get("name") or product.get("product_name") or "Unnamed Product"

            if name in seen_products:
                continue
            seen_products.add(name)

            sku = product.get("sku") or product.get("id") or product.get("product_id") or "-"
            issues = complaint_counts.get(name, product.get("issues") or product.get("complaint_count") or 0)
            warranty = product.get("warranty") or product.get("warranty_status") or "-"
            replacement = product.get("replacement_window") or product.get("replacement_policy") or "-"

            st.markdown(f"""
            <div class="product-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;">
                <div>
                  <div style="font-size:1rem;font-weight:800;color:#f5f9ff;margin-bottom:6px;">{esc(name)}</div>
                  <div style="font-size:.78rem;color:#93a6c8;">SKU / ID: {esc(sku)}</div>
                </div>
                <div class="rx-pill">{esc(product.get("category", "Product"))}</div>
              </div>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px;">
                <div class="mini-stat"><span>Complaints</span><strong>{esc(issues)}</strong></div>
                <div class="mini-stat"><span>Warranty</span><strong>{esc(warranty)}</strong></div>
                <div class="mini-stat"><span>Replacement</span><strong>{esc(replacement)}</strong></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
