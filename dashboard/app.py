import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

API_BASE = os.getenv("RESOLVEX_API_URL", "http://localhost:8080")
PORT = int(os.getenv("DASHBOARD_PORT", "8502"))

app = FastAPI(title="ResolveX Dashboard", version="13.0.0")

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ResolveX</title>
  <style>
    :root{
      --bg:#08111d;
      --bg-soft:#0e1728;
      --panel:#111c30;
      --panel-2:#0d1627;
      --line:rgba(120,150,230,.14);
      --line-2:rgba(255,255,255,.06);
      --text:#f4f8ff;
      --muted:#95a7c9;
      --blue:#5c85ff;
      --cyan:#55e6ff;
      --purple:#c86dff;
      --green:#4fffb0;
      --amber:#ffca63;
      --red:#ff6b7d;
      --pink:#ff5ccf;
      --radius:22px;
      --sidebar:230px;
      --shadow:0 18px 44px rgba(0,0,0,.30);
    }

    *{box-sizing:border-box}
    html,body{
      margin:0;
      padding:0;
      min-height:100%;
      color:var(--text);
      font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 10% 12%, rgba(92,133,255,.16), transparent 24%),
        radial-gradient(circle at 86% 18%, rgba(200,109,255,.10), transparent 24%),
        radial-gradient(circle at 50% 84%, rgba(85,230,255,.06), transparent 30%),
        linear-gradient(180deg,#07101c 0%, #0a1321 100%);
    }

    body::before{
      content:"";
      position:fixed;
      inset:0;
      pointer-events:none;
      background:
        linear-gradient(rgba(255,255,255,.017) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.017) 1px, transparent 1px);
      background-size:26px 26px;
      mask-image:linear-gradient(to bottom, rgba(255,255,255,.25), transparent 78%);
      opacity:.16;
    }

    .app{
      display:grid;
      grid-template-columns:var(--sidebar) 1fr;
      min-height:100vh;
      position:relative;
      z-index:1;
    }

    .sidebar{
      position:sticky;
      top:0;
      height:100vh;
      padding:18px 16px;
      background:linear-gradient(180deg, rgba(8,14,26,.98), rgba(7,11,20,.98));
      border-right:1px solid rgba(121,149,230,.12);
      display:flex;
      flex-direction:column;
      gap:14px;
    }

    .brand{
      display:flex;
      align-items:center;
      gap:12px;
      padding:4px 4px 10px;
    }

    .logo{
      width:44px;
      height:44px;
      border-radius:14px;
      display:grid;
      place-items:center;
      font-weight:800;
      color:white;
      background:linear-gradient(135deg,var(--blue),#79a1ff);
      box-shadow:0 0 0 1px rgba(255,255,255,.05), 0 0 28px rgba(92,133,255,.28);
    }

    .brand h1{
      margin:0;
      font-size:1rem;
      letter-spacing:-.02em;
    }

    .brand p{
      margin:4px 0 0;
      color:var(--muted);
      font-size:.78rem;
      line-height:1.3;
    }

    .side-label{
      color:#7f90b1;
      font-size:.71rem;
      font-weight:800;
      text-transform:uppercase;
      letter-spacing:.14em;
      padding:0 6px;
      margin-top:6px;
    }

    .nav{
      display:flex;
      flex-direction:column;
      gap:8px;
    }

    .nav-btn{
      width:100%;
      border:none;
      background:transparent;
      color:#deebff;
      padding:12px 12px;
      border-radius:14px;
      text-align:left;
      font:inherit;
      font-weight:700;
      cursor:pointer;
      transition:.18s ease;
      display:flex;
      align-items:center;
      gap:10px;
      position:relative;
    }

    .nav-btn:hover{ background:rgba(92,133,255,.06); }

    .nav-btn.active{
      background:linear-gradient(90deg, rgba(92,133,255,.18), rgba(85,230,255,.08));
      border:1px solid rgba(93,189,255,.22);
      box-shadow:inset 0 0 18px rgba(85,230,255,.05), 0 0 18px rgba(85,230,255,.07);
    }

    .nav-btn.active::after{
      content:"";
      position:absolute;
      right:8px;
      top:10px;
      bottom:10px;
      width:2px;
      border-radius:999px;
      background:linear-gradient(180deg,var(--cyan),transparent);
      box-shadow:0 0 10px var(--cyan);
    }

    .nav-icon{
      width:17px;
      height:17px;
      stroke:#bed3ff;
      stroke-width:1.8;
      fill:none;
      stroke-linecap:round;
      stroke-linejoin:round;
      flex:0 0 17px;
    }

    .side-card{
      border-radius:18px;
      border:1px solid rgba(108,140,220,.14);
      background:rgba(19,28,48,.72);
      padding:14px;
    }

    .status-head{
      display:flex;
      align-items:center;
      gap:8px;
      margin-bottom:8px;
    }

    .status-dot{
      width:8px;
      height:8px;
      border-radius:999px;
      background:var(--green);
      box-shadow:0 0 10px var(--green);
    }

    .side-card p{
      margin:0;
      color:var(--muted);
      font-size:.79rem;
      line-height:1.55;
      word-break:break-word;
    }

    .side-actions{
      margin-top:auto;
      display:flex;
      flex-direction:column;
      gap:10px;
    }

    .btn, .refresh-btn{
      border:none;
      border-radius:14px;
      background:linear-gradient(135deg,#5c85ff,#7ca4ff);
      color:white;
      padding:11px 14px;
      font:inherit;
      font-weight:800;
      cursor:pointer;
      transition:.18s ease;
    }

    .btn:hover, .refresh-btn:hover{ filter:brightness(1.05); }

    .btn.secondary{
      background:linear-gradient(180deg, rgba(34,48,79,.95), rgba(24,35,57,.95));
      border:1px solid rgba(127,177,255,.16);
    }

    .main{
      padding:22px 18px 30px;
    }

    .top{
      display:flex;
      justify-content:space-between;
      gap:18px;
      align-items:flex-start;
      margin-bottom:16px;
    }

    .hero h2{
      margin:0;
      font-size:2rem;
      letter-spacing:-.05em;
    }

    .hero p{
      margin:10px 0 0;
      color:#c6d6ee;
      line-height:1.6;
      max-width:980px;
      font-size:.98rem;
    }

    .meta{
      color:var(--muted);
      font-size:.83rem;
      white-space:nowrap;
    }

    .page{ display:none; }
    .page.active{ display:block; }

    .card{
      position:relative;
      overflow:hidden;
      border-radius:var(--radius);
      border:1px solid var(--line);
      background:linear-gradient(180deg, rgba(18,27,45,.96), rgba(12,19,33,.96));
      box-shadow:inset 0 1px 0 rgba(255,255,255,.04), var(--shadow);
      margin-bottom:12px;
    }

    .card::before{
      content:"";
      position:absolute;
      inset:0;
      background:linear-gradient(180deg, rgba(255,255,255,.03), transparent 40%);
      pointer-events:none;
    }

    .card-body{
      position:relative;
      z-index:1;
      padding:16px;
    }

    .section-head{
      display:flex;
      justify-content:space-between;
      align-items:flex-start;
      gap:12px;
      margin-bottom:12px;
    }

    .section-title{
      margin:0;
      font-size:1rem;
      font-weight:800;
      letter-spacing:-.02em;
    }

    .section-desc{
      color:var(--muted);
      font-size:.8rem;
      line-height:1.45;
      margin-top:4px;
    }

    .kpis{
      display:grid;
      grid-template-columns:repeat(6, minmax(0,1fr));
      gap:10px;
      margin-bottom:12px;
    }

    .kpi-title{
      font-size:.84rem;
      color:#eff6ff;
      margin-bottom:10px;
    }

    .kpi-num{
      font-size:1.8rem;
      font-weight:800;
      line-height:1;
      letter-spacing:-.05em;
    }

    .kpi-sub{
      margin-top:8px;
      color:var(--muted);
      font-size:.77rem;
      line-height:1.45;
    }

    .overview-grid{
      display:grid;
      grid-template-columns:1.22fr .78fr;
      gap:12px;
      margin-bottom:12px;
    }

    .right-stack{
      display:flex;
      flex-direction:column;
      gap:12px;
    }

    .chat-shell{
      display:flex;
      flex-direction:column;
      gap:10px;
      min-height:680px;
    }

    .chat-stream{
      display:flex;
      flex-direction:column;
      gap:10px;
      min-height:360px;
      max-height:560px;
      overflow:auto;
      padding-right:4px;
    }

    .msg{
      max-width:80%;
      padding:12px 13px;
      border-radius:16px;
      font-size:.86rem;
      line-height:1.5;
      border:1px solid rgba(255,255,255,.06);
      white-space:pre-wrap;
    }

    .msg.user{
      align-self:flex-end;
      background:rgba(92,133,255,.16);
      color:#edf4ff;
    }

    .msg.bot{
      align-self:flex-start;
      background:rgba(18,30,50,.92);
      color:#dce8f7;
    }

    .msg.system{
      align-self:center;
      background:rgba(85,230,255,.08);
      color:#b9f2ff;
      font-size:.8rem;
      border-radius:999px;
      padding:8px 12px;
      max-width:100%;
    }

    .chat-inputs{
      display:flex;
      flex-direction:column;
      gap:10px;
      margin-top:auto;
    }

    label{
      display:block;
      margin:12px 0 8px;
      color:#dbe7f7;
      font-size:.84rem;
      font-weight:700;
    }

    textarea, select, input{
      width:100%;
      border:1px solid rgba(255,255,255,.06);
      background:#0f1728;
      color:var(--text);
      border-radius:12px;
      padding:11px 12px;
      font:inherit;
      outline:none;
    }

    textarea{
      min-height:130px;
      resize:vertical;
    }

    .row{
      display:flex;
      gap:10px;
      flex-wrap:wrap;
    }

    .trace-box{
      display:flex;
      flex-direction:column;
      gap:8px;
      max-height:300px;
      overflow:auto;
    }

    .trace-line{
      display:flex;
      justify-content:space-between;
      gap:10px;
      padding:10px 12px;
      border-radius:12px;
      border:1px solid rgba(255,255,255,.05);
      background:rgba(6,10,18,.48);
      font-size:.83rem;
    }

    .trace-left{
      color:#d8e6fb;
      white-space:pre-wrap;
    }

    .trace-right{
      font-weight:800;
      color:#abf8ca;
      flex:0 0 auto;
    }

    .feed{
      display:flex;
      flex-direction:column;
      gap:8px;
      max-height:280px;
      overflow:auto;
    }

    .feed-item{
      display:flex;
      gap:10px;
      padding:10px 12px;
      border-radius:12px;
      border:1px solid rgba(255,255,255,.05);
      background:rgba(17,24,40,.78);
    }

    .feed-dot{
      width:8px;
      height:8px;
      border-radius:999px;
      margin-top:7px;
      flex:0 0 8px;
      background:var(--cyan);
      box-shadow:0 0 10px var(--cyan);
    }

    .feed-time{
      color:#8da2c6;
      font-size:.72rem;
      margin-bottom:3px;
    }

    .feed-text{
      color:#dbe7f7;
      font-size:.8rem;
      line-height:1.45;
    }

    .ops-grid{
      display:grid;
      grid-template-columns:.9fr 1.1fr;
      gap:12px;
      margin-bottom:12px;
    }

    .status-list, .tool-grid{
      display:flex;
      flex-direction:column;
      gap:10px;
    }

    .status-item{
      display:flex;
      gap:10px;
      align-items:flex-start;
      padding:10px 12px;
      border-radius:14px;
      border:1px solid rgba(255,255,255,.06);
      background:rgba(17,24,40,.82);
    }

    .status-indicator{
      width:10px;
      height:10px;
      border-radius:999px;
      margin-top:5px;
      flex:0 0 10px;
    }

    .pending{ background:#7c8aa6; }
    .running{ background:#55e6ff; box-shadow:0 0 12px #55e6ff; }
    .done{ background:#4fffb0; box-shadow:0 0 12px #4fffb0; }
    .error{ background:#ff6b7d; box-shadow:0 0 12px #ff6b7d; }

    .status-title{
      font-size:.85rem;
      font-weight:800;
      margin-bottom:3px;
    }

    .status-text{
      font-size:.77rem;
      color:var(--muted);
      line-height:1.45;
    }

    .tool-card{
      padding:12px;
      border-radius:14px;
      border:1px solid rgba(255,255,255,.06);
      background:rgba(17,24,40,.82);
    }

    .tool-head{
      display:flex;
      justify-content:space-between;
      gap:12px;
      margin-bottom:8px;
    }

    .tool-title{
      font-size:.86rem;
      font-weight:800;
    }

    .tool-badge{
      font-size:.72rem;
      color:#bcecff;
      border:1px solid rgba(85,230,255,.2);
      background:rgba(85,230,255,.08);
      border-radius:999px;
      padding:4px 8px;
    }

    .tool-text{
      font-size:.78rem;
      line-height:1.5;
      color:var(--muted);
      white-space:pre-wrap;
      word-break:break-word;
    }

    .mini-grid{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:12px;
      margin-bottom:12px;
    }

    .calendar-header{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:10px;
    }

    .cal-title{
      font-weight:800;
      font-size:.92rem;
    }

    .calendar-grid{
      display:grid;
      grid-template-columns:repeat(7,1fr);
      gap:8px;
    }

    .cal-day-name{
      text-align:center;
      font-size:.72rem;
      color:var(--muted);
      font-weight:700;
      padding-bottom:4px;
    }

    .cal-cell{
      min-height:72px;
      border-radius:14px;
      border:1px solid rgba(255,255,255,.05);
      background:rgba(12,18,32,.6);
      padding:8px;
      display:flex;
      flex-direction:column;
      gap:6px;
    }

    .cal-cell.dim{ opacity:.35; }
    .cal-cell.today{
      border-color:rgba(85,230,255,.32);
      box-shadow:0 0 14px rgba(85,230,255,.08);
    }

    .cal-date{
      font-size:.76rem;
      font-weight:800;
      color:#dce7f7;
    }

    .cal-pill{
      border-radius:999px;
      padding:4px 7px;
      font-size:.68rem;
      font-weight:700;
      background:rgba(92,133,255,.16);
      color:#ddecff;
      border:1px solid rgba(92,133,255,.14);
      overflow:hidden;
      text-overflow:ellipsis;
      white-space:nowrap;
    }

    .kanban{
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      gap:10px;
    }

    .kan-col{
      border-radius:16px;
      border:1px solid rgba(255,255,255,.05);
      background:rgba(13,19,33,.72);
      padding:12px;
      min-height:260px;
    }

    .kan-head{
      display:flex;
      justify-content:space-between;
      margin-bottom:10px;
      font-size:.82rem;
      font-weight:800;
    }

    .kan-list{
      display:flex;
      flex-direction:column;
      gap:8px;
    }

    .task-card{
      border-radius:12px;
      border:1px solid rgba(255,255,255,.05);
      background:rgba(18,27,45,.92);
      padding:10px;
    }

    .task-card strong{
      display:block;
      font-size:.8rem;
      margin-bottom:4px;
    }

    .task-card span{
      display:block;
      color:var(--muted);
      font-size:.72rem;
      line-height:1.4;
    }

    .bars{
      display:flex;
      flex-direction:column;
      gap:10px;
      margin-top:4px;
    }

    .bar-row{
      display:grid;
      grid-template-columns:132px 1fr 40px;
      gap:10px;
      align-items:center;
    }

    .bar-label{
      font-size:.84rem;
      color:#d9e6f7;
    }

    .bar-track{
      height:14px;
      border-radius:999px;
      border:1px solid rgba(255,255,255,.08);
      background:rgba(255,255,255,.02);
      overflow:hidden;
    }

    .bar-fill{
      height:100%;
      border-radius:999px;
      box-shadow:0 0 16px currentColor;
    }

    .bar-value{
      text-align:right;
      font-weight:800;
      font-size:.8rem;
    }

    .donut-wrap{
      display:flex;
      align-items:center;
      justify-content:center;
      min-height:240px;
      position:relative;
    }

    .donut-center{
      position:absolute;
      text-align:center;
      pointer-events:none;
    }

    .donut-center .big{
      font-size:1.35rem;
      font-weight:800;
    }

    .donut-center .small{
      font-size:.76rem;
      color:var(--muted);
      margin-top:4px;
    }

    .donut-legend{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:8px 12px;
      margin-top:8px;
    }

    .legend-item{
      display:flex;
      align-items:center;
      gap:8px;
      color:#d6e3f6;
      font-size:.82rem;
    }

    .legend-dot{
      width:10px;
      height:10px;
      border-radius:999px;
      flex:0 0 10px;
      box-shadow:0 0 12px currentColor;
    }

    .filters{
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      gap:10px;
      margin-bottom:12px;
    }

    .table-wrap{
      overflow:auto;
      border:1px solid rgba(255,255,255,.06);
      border-radius:14px;
      background:rgba(12,18,32,.7);
    }

    table{
      width:100%;
      border-collapse:collapse;
      min-width:860px;
    }

    th, td{
      padding:13px 12px;
      text-align:left;
      border-bottom:1px solid rgba(255,255,255,.05);
      font-size:.86rem;
      vertical-align:top;
    }

    th{
      background:#0f1728;
      color:var(--muted);
      font-size:.72rem;
      text-transform:uppercase;
      letter-spacing:.06em;
      font-weight:800;
      position:sticky;
      top:0;
    }

    tr:last-child td{ border-bottom:none; }

    .product-list{
      display:flex;
      flex-direction:column;
      gap:12px;
    }

    .product-card{
      border-radius:16px;
      border:1px solid rgba(255,255,255,.06);
      background:rgba(15,23,40,.86);
      padding:14px;
    }

    .product-top{
      display:flex;
      justify-content:space-between;
      gap:16px;
      align-items:flex-start;
      margin-bottom:12px;
    }

    .product-title{
      font-size:.95rem;
      font-weight:800;
      margin-bottom:5px;
    }

    .product-sub{
      color:var(--muted);
      font-size:.8rem;
    }

    .product-stats{
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      gap:8px;
      margin-bottom:12px;
    }

    .mini-stat{
      border-radius:12px;
      border:1px solid rgba(255,255,255,.05);
      background:#111a2d;
      padding:10px;
    }

    .mini-stat span{
      display:block;
      color:var(--muted);
      font-size:.72rem;
      margin-bottom:5px;
    }

    .mini-stat strong{
      font-size:.9rem;
      font-weight:800;
    }

    .pill-row{
      display:flex;
      flex-wrap:wrap;
      gap:8px;
      margin-top:10px;
    }

    .pill{
      border:1px solid rgba(255,255,255,.06);
      background:#111a2d;
      border-radius:999px;
      padding:7px 10px;
      font-size:.75rem;
      color:#dce7f7;
    }

    .empty{
      color:var(--muted);
      font-size:.84rem;
      padding:4px 0;
    }

    @media (max-width: 1450px){
      .kpis{ grid-template-columns:repeat(3,minmax(0,1fr)); }
    }

    @media (max-width: 1320px){
      .overview-grid, .ops-grid, .mini-grid{ grid-template-columns:1fr; }
      .kanban{ grid-template-columns:1fr 1fr; }
    }

    @media (max-width: 980px){
      .app{ grid-template-columns:1fr; }
      .sidebar{
        position:relative;
        height:auto;
        border-right:none;
        border-bottom:1px solid rgba(121,149,230,.14);
      }
      .filters, .product-stats, .kpis{ grid-template-columns:1fr 1fr; }
    }

    @media (max-width: 700px){
      .top{ flex-direction:column; }
      .filters, .product-stats, .kpis, .kanban{ grid-template-columns:1fr; }
      .bar-row{ grid-template-columns:1fr; }
      .msg{ max-width:92%; }
      .calendar-grid{ gap:6px; }
      .cal-cell{ min-height:64px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="logo">R</div>
        <div>
          <h1>ResolveX</h1>
          <p>Customer Care Intelligence</p>
        </div>
      </div>

      <div class="side-label">Navigation</div>
      <div class="nav">
        <button class="nav-btn active" data-page="overview">
          <svg class="nav-icon" viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"></path><path d="M5 9.5V21h14V9.5"></path></svg>
          <span>Overview</span>
        </button>
        <button class="nav-btn" data-page="operations">
          <svg class="nav-icon" viewBox="0 0 24 24"><path d="M4 5h16v14H4z"></path><path d="M8 9h8"></path><path d="M8 13h5"></path></svg>
          <span>Operations</span>
        </button>
        <button class="nav-btn" data-page="complaints">
          <svg class="nav-icon" viewBox="0 0 24 24"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
          <span>Complaints</span>
        </button>
        <button class="nav-btn" data-page="products">
          <svg class="nav-icon" viewBox="0 0 24 24"><path d="M3 7.5 12 3l9 4.5-9 4.5-9-4.5Z"></path><path d="M3 7.5V16.5L12 21l9-4.5V7.5"></path><path d="M12 12v9"></path></svg>
          <span>Products</span>
        </button>
      </div>

      <div class="side-label">System</div>
      <div class="side-card">
        <div class="status-head">
          <span class="status-dot"></span>
          <strong>Operational</strong>
        </div>
        <p>Interactive complaint chat, workflow trace, tasks, notes, calendar, and product escalation view.</p>
      </div>

      <div class="side-card">
        <p id="apiStatus">API: __API_BASE__</p>
      </div>

      <div class="side-actions">
        <button id="refreshBtn" class="refresh-btn">Refresh data</button>
      </div>
    </aside>

    <main class="main">
      <div class="top">
        <div class="hero">
          <h2>ResolveX Command Center</h2>
          <p>
            Clean, interactive dashboard for complaints, AI responses, notes, tasks, calendar follow-ups,
            and manufacturer escalation tracking.
          </p>
        </div>
        <div class="meta" id="lastUpdated">Last updated: --</div>
      </div>

      <section id="page-overview" class="page active">
        <div class="kpis">
          <div class="card"><div class="card-body"><div class="kpi-title">Total complaints</div><div class="kpi-num" id="kpiTotal">0</div><div class="kpi-sub">All logged cases.</div></div></div>
          <div class="card"><div class="card-body"><div class="kpi-title">Active tickets</div><div class="kpi-num" id="kpiActive">0</div><div class="kpi-sub">Still in progress.</div></div></div>
          <div class="card"><div class="card-body"><div class="kpi-title">Resolved</div><div class="kpi-num" id="kpiResolved">0</div><div class="kpi-sub">Completed by workflow.</div></div></div>
          <div class="card"><div class="card-body"><div class="kpi-title">Escalated</div><div class="kpi-num" id="kpiEscalated">0</div><div class="kpi-sub">Escalation path used.</div></div></div>
          <div class="card"><div class="card-body"><div class="kpi-title">Manufacturer cases</div><div class="kpi-num" id="kpiManufacturer">0</div><div class="kpi-sub">Upstream product issues.</div></div></div>
          <div class="card"><div class="card-body"><div class="kpi-title">SLA overdue</div><div class="kpi-num" id="kpiOverdue">0</div><div class="kpi-sub">Past ETA and open.</div></div></div>
        </div>

        <div class="overview-grid">
          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">Customer Portal Chat</div>
                  <div class="section-desc">Talk to the system and submit a real complaint through the backend.</div>
                </div>
              </div>

              <div class="chat-shell">
                <div id="chatStream" class="chat-stream">
                  <div class="msg system">ResolveX chat ready</div>
                  <div class="msg bot">Hi. Tell me what happened with your order, and I’ll help you through it.</div>
                </div>

                <div class="chat-inputs">
                  <label for="sampleComplaint">Sample complaint</label>
                  <select id="sampleComplaint">
                    <option value="">Custom...</option>
                    <option>My Voltix Charger overheats after five minutes and stopped working. Order #ORD001.</option>
                    <option>I received the wrong AeroBuds Pro color and the box was already damaged. Order #ORD003.</option>
                    <option>The Nova Blender has a broken motor and makes a burning smell after two uses. Order #ORD002.</option>
                    <option>My headphones stopped charging after only 2 weeks and I am very frustrated. Order #ORD003.</option>
                  </select>

                  <label for="complaintInput">Customer complaint</label>
                  <textarea id="complaintInput" placeholder="Describe the issue here..."></textarea>

                  <div class="row">
                    <button id="submitComplaintBtn" class="btn">Send Complaint</button>
                    <button id="resetBtn" class="btn secondary">Reset Chat</button>
                    <button id="trackerBtn" class="btn secondary">Run Tracker</button>
                    <button id="learningBtn" class="btn secondary">Run Learning</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="right-stack">
            <div class="card">
              <div class="card-body">
                <div class="section-head">
                  <div>
                    <div class="section-title">AI Thought Trace</div>
                    <div class="section-desc">Readable workflow progression.</div>
                  </div>
                </div>
                <div id="traceBox" class="trace-box"></div>
              </div>
            </div>

            <div class="card">
              <div class="card-body">
                <div class="section-head">
                  <div>
                    <div class="section-title">Live Activity Feed</div>
                    <div class="section-desc">Recent workflow events.</div>
                  </div>
                </div>
                <div id="activityFeed" class="feed"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="mini-grid">
          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">Resolution Breakdown</div>
                  <div class="section-desc">Case outcome mix.</div>
                </div>
              </div>
              <div id="resolutionBars" class="bars"></div>
            </div>
          </div>

          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">Issue Type Distribution</div>
                  <div class="section-desc">Current complaint categories.</div>
                </div>
              </div>
              <div class="donut-wrap">
                <svg id="donutSvg" width="260" height="220" viewBox="0 0 260 220"></svg>
                <div class="donut-center">
                  <div class="big" id="donutTotal">0</div>
                  <div class="small">Issues tracked</div>
                </div>
              </div>
              <div id="donutLegend" class="donut-legend"></div>
            </div>
          </div>
        </div>
      </section>

      <section id="page-operations" class="page">
        <div class="ops-grid">
          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">System Status</div>
                  <div class="section-desc">Current subsystem state.</div>
                </div>
              </div>
              <div id="statusList" class="status-list"></div>
            </div>
          </div>

          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">Operational Panels</div>
                  <div class="section-desc">Notes, tasks, calendar, manufacturer, and tracker output.</div>
                </div>
              </div>
              <div id="toolGrid" class="tool-grid"></div>
            </div>
          </div>
        </div>

        <div class="mini-grid">
          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">Calendar</div>
                  <div class="section-desc">Estimated due dates and follow-up reminders.</div>
                </div>
              </div>
              <div class="calendar-header">
                <div class="cal-title" id="calendarMonthLabel">Calendar</div>
              </div>
              <div id="calendarGrid"></div>
            </div>
          </div>

          <div class="card">
            <div class="card-body">
              <div class="section-head">
                <div>
                  <div class="section-title">Task Board</div>
                  <div class="section-desc">Derived from real case state.</div>
                </div>
              </div>
              <div id="kanbanBoard" class="kanban"></div>
            </div>
          </div>
        </div>
      </section>

      <section id="page-complaints" class="page">
        <div class="card">
          <div class="card-body">
            <div class="section-head">
              <div>
                <div class="section-title">Complaints</div>
                <div class="section-desc">Filter complaints by product, issue, urgency, and resolution.</div>
              </div>
            </div>

            <div class="filters">
              <select id="filterProduct"></select>
              <select id="filterResolution"></select>
              <select id="filterUrgency">
                <option value="All">All urgencies</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <select id="filterIssue"></select>
            </div>

            <div id="complaintsTable" class="table-wrap"></div>
          </div>
        </div>
      </section>

      <section id="page-products" class="page">
        <div class="card">
          <div class="card-body">
            <div class="section-head">
              <div>
                <div class="section-title">Products</div>
                <div class="section-desc">Product-level complaint and escalation monitoring.</div>
              </div>
            </div>
            <div id="productCards" class="product-list"></div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const API_BASE = "__API_BASE__";

    let dashboardData = {};
    let complaintsData = [];
    let productsData = [];
    let manufacturerPending = [];

    let liveContext = { lastComplaintId: null, lastProductName: null };
    let traceItems = [];
    let activityItems = [];
    let liveStatuses = [];
    let liveTools = {};

    function nowTime() {
      return new Date().toLocaleTimeString();
    }

    function setLastUpdated() {
      document.getElementById("lastUpdated").textContent = "Last updated: " + new Date().toLocaleString();
    }

    function activatePage(pageName) {
      document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("page-" + pageName).classList.add("active");
      document.querySelector('.nav-btn[data-page="' + pageName + '"]').classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    async function apiGet(path) {
      const r = await fetch(`${API_BASE}${path}`);
      const text = await r.text();
      let data = null;
      try { data = JSON.parse(text); } catch { data = { raw: text }; }
      return { ok: r.ok, status: r.status, data };
    }

    async function apiPost(path, payload) {
      const r = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const text = await r.text();
      let data = null;
      try { data = JSON.parse(text); } catch { data = { raw: text }; }
      return { ok: r.ok, status: r.status, data };
    }

    function appendChatMessage(type, text) {
      const stream = document.getElementById("chatStream");
      const div = document.createElement("div");
      div.className = "msg " + type;
      div.textContent = text;
      stream.appendChild(div);
      stream.scrollTop = stream.scrollHeight;
    }

    function pushTrace(text, status="OK") {
      traceItems.unshift({ text, status });
      traceItems = traceItems.slice(0, 8);
      renderTrace();
    }

    function renderTrace() {
      const box = document.getElementById("traceBox");
      box.innerHTML = traceItems.length
        ? traceItems.map(item => `
            <div class="trace-line">
              <div class="trace-left">&gt; ${item.text}</div>
              <div class="trace-right">[${item.status}]</div>
            </div>
          `).join("")
        : '<div class="empty">No trace yet.</div>';
    }

    function pushActivity(text) {
      activityItems.unshift({ time: nowTime(), text });
      activityItems = activityItems.slice(0, 16);
      renderActivity();
    }

    function renderActivity() {
      const wrap = document.getElementById("activityFeed");
      wrap.innerHTML = activityItems.length
        ? activityItems.map(item => `
            <div class="feed-item">
              <div class="feed-dot"></div>
              <div>
                <div class="feed-time">${item.time}</div>
                <div class="feed-text">${item.text}</div>
              </div>
            </div>
          `).join("")
        : '<div class="empty">No activity yet.</div>';
    }

    function initSystemPanels() {
      liveStatuses = [
        { key:"listener", title:"Listener Agent", text:"Waiting for complaint.", state:"pending" },
        { key:"analyst", title:"Analyst Agent", text:"Waiting for eligibility check.", state:"pending" },
        { key:"decision", title:"Decision Agent", text:"Waiting for resolution decision.", state:"pending" },
        { key:"database", title:"Database", text:"Waiting for case log.", state:"pending" },
        { key:"notes", title:"Notes", text:"Waiting for notes visibility.", state:"pending" },
        { key:"tasks", title:"Tasks", text:"Waiting for task visibility.", state:"pending" },
        { key:"calendar", title:"Calendar", text:"Waiting for follow-up schedule.", state:"pending" },
        { key:"manufacturer", title:"Manufacturer", text:"Waiting for manufacturer state.", state:"pending" },
        { key:"tracker", title:"Tracker", text:"Tracker not run yet.", state:"pending" },
        { key:"customer", title:"Customer Portal", text:"No final response yet.", state:"pending" }
      ];

      liveTools = {
        notes:{ title:"Notes", badge:"Connected", body:"No notes loaded yet." },
        tasks:{ title:"Tasks", badge:"Connected", body:"No tasks loaded yet." },
        calendar:{ title:"Calendar", badge:"Connected", body:"No calendar items loaded yet." },
        manufacturer:{ title:"Manufacturer", badge:"Connected", body:"No manufacturer data loaded yet." },
        tracker:{ title:"Tracker", badge:"Connected", body:"Tracker has not been run yet." }
      };
    }

    function renderStatuses() {
      const wrap = document.getElementById("statusList");
      wrap.innerHTML = liveStatuses.map(item => `
        <div class="status-item">
          <div class="status-indicator ${item.state}"></div>
          <div>
            <div class="status-title">${item.title}</div>
            <div class="status-text">${item.text}</div>
          </div>
        </div>
      `).join("");
    }

    function setStatus(key, state, text) {
      const item = liveStatuses.find(x => x.key === key);
      if (!item) return;
      item.state = state;
      item.text = text;
      renderStatuses();
    }

    function renderTools() {
      const wrap = document.getElementById("toolGrid");
      wrap.innerHTML = Object.values(liveTools).map(item => `
        <div class="tool-card">
          <div class="tool-head">
            <div class="tool-title">${item.title}</div>
            <div class="tool-badge">${item.badge}</div>
          </div>
          <div class="tool-text">${item.body}</div>
        </div>
      `).join("");
    }

    function setTool(key, body, badge="Connected") {
      if (!liveTools[key]) return;
      liveTools[key].body = body;
      liveTools[key].badge = badge;
      renderTools();
    }

    function resetChat() {
      document.getElementById("chatStream").innerHTML = `
        <div class="msg system">ResolveX chat ready</div>
        <div class="msg bot">Hi. Tell me what happened with your order, and I’ll help you through it.</div>
      `;
      traceItems = [];
      activityItems = [];
      liveContext = { lastComplaintId: null, lastProductName: null };
      initSystemPanels();
      renderTrace();
      renderActivity();
      renderStatuses();
      renderTools();
    }

    function makeBarList(containerId, dataObj) {
      const container = document.getElementById(containerId);
      const entries = Object.entries(dataObj || {});
      if (!entries.length) {
        container.innerHTML = '<div class="empty">No data available.</div>';
        return;
      }

      const colors = ["#55e6ff", "#c86dff", "#ff5ccf", "#ffca63", "#5c85ff", "#4fffb0"];
      const max = Math.max(...entries.map(([, v]) => Number(v || 0)), 1);

      container.innerHTML = entries.map(([label, value], i) => {
        const pct = (Number(value || 0) / max) * 100;
        const color = colors[i % colors.length];
        return `
          <div class="bar-row">
            <div class="bar-label">${label}</div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${pct}%; background:${color}; color:${color};"></div>
            </div>
            <div class="bar-value">${value}</div>
          </div>
        `;
      }).join("");
    }

    function renderDonut(dataObj) {
      const svg = document.getElementById("donutSvg");
      const legend = document.getElementById("donutLegend");
      const totalEl = document.getElementById("donutTotal");

      const entries = Object.entries(dataObj || {});
      if (!entries.length) {
        svg.innerHTML = "";
        legend.innerHTML = '<div class="empty">No data available.</div>';
        totalEl.textContent = "0";
        return;
      }

      const colors = ["#ff6b7d", "#5c85ff", "#55e6ff", "#ffca63", "#c86dff", "#4fffb0"];
      const total = entries.reduce((sum, [, v]) => sum + Number(v || 0), 0);
      totalEl.textContent = total;

      const cx = 130, cy = 110, r = 68, stroke = 26;
      let offset = 0;

      svg.innerHTML = entries.map(([label, value], i) => {
        const pct = (Number(value || 0) / Math.max(total, 1)) * 100;
        const len = pct * 4.272;
        const color = colors[i % colors.length];
        const part = `
          <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
            stroke="${color}" stroke-width="${stroke}" stroke-linecap="round"
            stroke-dasharray="${len} 427.2" stroke-dashoffset="${-offset}"
            transform="rotate(-90 ${cx} ${cy})"
            style="filter: drop-shadow(0 0 10px ${color});"></circle>
        `;
        offset += len;
        return part;
      }).join("") + `
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(255,255,255,.07)" stroke-width="${stroke}" stroke-dasharray="427.2 427.2"></circle>
      `;

      legend.innerHTML = entries.map(([label, value], i) => {
        const color = colors[i % colors.length];
        return `<div class="legend-item"><span class="legend-dot" style="background:${color}; color:${color};"></span><span>${label} ${value}</span></div>`;
      }).join("");
    }

    function makeTable(data, columns, labels = {}) {
      if (!data || !data.length) return '<div class="empty">No data available.</div>';
      const thead = columns.map(col => `<th>${labels[col] || col}</th>`).join("");
      const tbody = data.map(row => `<tr>${columns.map(col => `<td>${row[col] ?? "—"}</td>`).join("")}</tr>`).join("");
      return `<table><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
    }

    function renderKPIs() {
      const summary = dashboardData.summary || {};
      const resolution = dashboardData.resolution_breakdown || {};
      const total = summary.total_complaints ?? complaintsData.length ?? 0;
      const resolved = complaintsData.filter(c => c.is_resolved === true || c.resolution).length;
      const active = complaintsData.filter(c => !c.loop_closed_at).length;
      const escalated = resolution.escalate || 0;
      const overdue = complaintsData.filter(c => {
        const eta = Number(c.estimated_resolution_days || 0);
        if (!eta || !c.created_at) return false;
        const created = new Date(c.created_at);
        const due = new Date(created.getTime() + eta * 24 * 60 * 60 * 1000);
        return Date.now() > due.getTime() && !c.loop_closed_at;
      }).length;

      document.getElementById("kpiTotal").textContent = total;
      document.getElementById("kpiActive").textContent = active;
      document.getElementById("kpiResolved").textContent = resolved;
      document.getElementById("kpiEscalated").textContent = escalated;
      document.getElementById("kpiManufacturer").textContent = manufacturerPending.length || summary.manufacturer_contacted || 0;
      document.getElementById("kpiOverdue").textContent = overdue;
    }

    function populateFilters() {
      const productSelect = document.getElementById("filterProduct");
      const resolutionSelect = document.getElementById("filterResolution");
      const issueSelect = document.getElementById("filterIssue");

      const products = [...new Set(complaintsData.map(c => c.product_name).filter(Boolean))].sort();
      const resolutions = [...new Set(complaintsData.map(c => c.resolution).filter(Boolean))].sort();
      const issues = [...new Set(complaintsData.map(c => c.issue_type).filter(Boolean))].sort();

      productSelect.innerHTML = `<option value="All">All products</option>` + products.map(v => `<option value="${v}">${v}</option>`).join("");
      resolutionSelect.innerHTML = `<option value="All">All resolutions</option>` + resolutions.map(v => `<option value="${v}">${v}</option>`).join("");
      issueSelect.innerHTML = `<option value="All">All issue types</option>` + issues.map(v => `<option value="${v}">${v}</option>`).join("");
    }

    function renderComplaints() {
      const product = document.getElementById("filterProduct").value;
      const resolution = document.getElementById("filterResolution").value;
      const urgency = document.getElementById("filterUrgency").value;
      const issue = document.getElementById("filterIssue").value;

      let filtered = [...complaintsData];
      if (product !== "All") filtered = filtered.filter(c => c.product_name === product);
      if (resolution !== "All") filtered = filtered.filter(c => c.resolution === resolution);
      if (urgency !== "All") filtered = filtered.filter(c => c.urgency_level === urgency);
      if (issue !== "All") filtered = filtered.filter(c => c.issue_type === issue);

      filtered.sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")));

      document.getElementById("complaintsTable").innerHTML = makeTable(
        filtered,
        ["complaint_id", "product_name", "issue_type", "urgency_level", "customer_emotion", "resolution", "priority", "estimated_resolution_days", "created_at"],
        { complaint_id:"ID", product_name:"Product", issue_type:"Issue", urgency_level:"Urgency", customer_emotion:"Emotion", resolution:"Resolution", priority:"Priority", estimated_resolution_days:"ETA", created_at:"Created" }
      );
    }

    function renderProducts() {
      const wrap = document.getElementById("productCards");
      if (!productsData.length) {
        wrap.innerHTML = '<div class="empty">No product data available.</div>';
        return;
      }

      wrap.innerHTML = productsData.map(prod => {
        const total = prod.total_complaints || 0;
        const contacted = !!prod.manufacturer_contacted;
        const resolved = !!prod.manufacturer_resolved;
        const pattern = !!prod.pattern_detected;

        return `
          <div class="product-card">
            <div class="product-top">
              <div>
                <div class="product-title">${prod.product_name}</div>
                <div class="product-sub">${resolved ? "Manufacturer resolved" : contacted ? "Manufacturer contacted" : total >= 3 ? "Needs escalation" : "Monitoring"}</div>
              </div>
              ${contacted && !resolved ? `<button class="btn resolve-btn" data-product="${prod.product_name}">Mark resolved</button>` : ""}
            </div>

            <div class="product-stats">
              <div class="mini-stat"><span>Total complaints</span><strong>${total}</strong></div>
              <div class="mini-stat"><span>Pattern detected</span><strong>${pattern ? "Yes" : "No"}</strong></div>
              <div class="mini-stat"><span>Mfr contacted</span><strong>${contacted ? "Yes" : "No"}</strong></div>
              <div class="mini-stat"><span>Mfr resolved</span><strong>${resolved ? "Yes" : "No"}</strong></div>
            </div>

            <div class="pill-row">
              <div class="pill">Product: ${prod.product_name}</div>
              <div class="pill">Complaints: ${total}</div>
              <div class="pill">Pattern: ${pattern ? "Detected" : "No"}</div>
            </div>
          </div>
        `;
      }).join("");

      document.querySelectorAll(".resolve-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const product = btn.dataset.product;
          btn.disabled = true;
          btn.textContent = "Updating...";
          pushTrace(`Marking manufacturer issue resolved for ${product}`, "RUN");
          pushActivity(`Manufacturer resolution requested for ${product}`);
          const res = await apiPost("/manufacturer/resolve", { product_name: product });
          if (res.ok && res.data.success) {
            appendChatMessage("system", `Manufacturer issue marked resolved for ${product}.`);
            pushTrace(`Manufacturer issue resolved for ${product}`, "OK");
            pushActivity(`Manufacturer issue resolved for ${product}`);
            await loadAllData();
          } else {
            appendChatMessage("system", `Failed to mark manufacturer issue resolved for ${product}.`);
            pushTrace(`Manufacturer resolve failed for ${product}`, "ERR");
          }
          btn.disabled = false;
          btn.textContent = "Mark resolved";
        });
      });
    }

    function deriveTasks() {
      const tasks = [];
      complaintsData.forEach(c => {
        const base = {
          id: c.complaint_id || "—",
          title: c.product_name || "Unknown product",
          detail: `${c.issue_type || "issue"} · ${c.urgency_level || "unknown"} urgency`
        };

        if (c.loop_closed_at) tasks.push({ col:"resolved", ...base });
        else if ((c.resolution || "").toLowerCase().includes("escalate")) tasks.push({ col:"escalated", ...base });
        else if (c.manufacturer_contacted) tasks.push({ col:"waiting", ...base });
        else tasks.push({ col:"review", ...base });
      });

      manufacturerPending.forEach(m => {
        tasks.push({
          col: m.issue_resolved ? "resolved" : "waiting",
          id: m.product_name || "—",
          title: `Manufacturer: ${m.product_name || "Unknown"}`,
          detail: `Email sent: ${m.email_sent ? "yes" : "no"} · Follow-ups: ${m.follow_up_count || 0}`
        });
      });

      return tasks.slice(0, 20);
    }

    function renderKanban() {
      const board = document.getElementById("kanbanBoard");
      const tasks = deriveTasks();

      const cols = [
        { key:"review", label:"In Review" },
        { key:"waiting", label:"Waiting" },
        { key:"escalated", label:"Escalated" },
        { key:"resolved", label:"Resolved" }
      ];

      board.innerHTML = cols.map(col => {
        const items = tasks.filter(t => t.col === col.key);
        return `
          <div class="kan-col">
            <div class="kan-head">
              <span>${col.label}</span>
              <span>${items.length}</span>
            </div>
            <div class="kan-list">
              ${items.length ? items.map(item => `
                <div class="task-card">
                  <strong>${item.title}</strong>
                  <span>${item.id}</span>
                  <span>${item.detail}</span>
                </div>
              `).join("") : '<div class="empty">No items</div>'}
            </div>
          </div>
        `;
      }).join("");
    }

    function deriveCalendarEvents() {
      const events = [];

      complaintsData.forEach(c => {
        if (!c.created_at || !c.estimated_resolution_days) return;
        const created = new Date(c.created_at);
        if (Number.isNaN(created.getTime())) return;
        const due = new Date(created.getTime() + Number(c.estimated_resolution_days || 0) * 24 * 60 * 60 * 1000);
        events.push({ date: due, label: (c.product_name || "Case") + " due" });
      });

      manufacturerPending.forEach(m => {
        const base = m.updated_at || m.contacted_at || m.created_at;
        if (!base) return;
        const d = new Date(base);
        if (Number.isNaN(d.getTime())) return;
        d.setDate(d.getDate() + 1);
        events.push({ date: d, label: (m.product_name || "Manufacturer") + " follow-up" });
      });

      return events.slice(0, 30);
    }

    function renderCalendar() {
      const gridWrap = document.getElementById("calendarGrid");
      const label = document.getElementById("calendarMonthLabel");

      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth();

      label.textContent = today.toLocaleString(undefined, { month: "long", year: "numeric" });

      const firstDay = new Date(year, month, 1);
      const startWeekday = firstDay.getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const prevMonthDays = new Date(year, month, 0).getDate();

      const events = deriveCalendarEvents();
      const eventMap = {};
      events.forEach(ev => {
        const key = ev.date.toISOString().slice(0, 10);
        if (!eventMap[key]) eventMap[key] = [];
        eventMap[key].push(ev);
      });

      const names = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
      let html = '<div class="calendar-grid">' + names.map(n => `<div class="cal-day-name">${n}</div>`).join("");

      const totalCells = 42;
      for (let i = 0; i < totalCells; i++) {
        let dayNum, cellDate, dim = false;

        if (i < startWeekday) {
          dayNum = prevMonthDays - startWeekday + i + 1;
          cellDate = new Date(year, month - 1, dayNum);
          dim = true;
        } else if (i >= startWeekday + daysInMonth) {
          dayNum = i - (startWeekday + daysInMonth) + 1;
          cellDate = new Date(year, month + 1, dayNum);
          dim = true;
        } else {
          dayNum = i - startWeekday + 1;
          cellDate = new Date(year, month, dayNum);
        }

        const key = cellDate.toISOString().slice(0, 10);
        const dayEvents = eventMap[key] || [];
        const isToday =
          cellDate.getFullYear() === today.getFullYear() &&
          cellDate.getMonth() === today.getMonth() &&
          cellDate.getDate() === today.getDate();

        html += `
          <div class="cal-cell ${dim ? 'dim' : ''} ${isToday ? 'today' : ''}">
            <div class="cal-date">${dayNum}</div>
            ${dayEvents.slice(0,2).map(ev => `<div class="cal-pill">${ev.label}</div>`).join("")}
          </div>
        `;
      }

      html += '</div>';
      gridWrap.innerHTML = html;
    }

    function deriveNotes() {
      const notes = complaintsData.slice(0, 4).map(c =>
        `Case ${c.complaint_id || "—"} · ${c.product_name || "Unknown"} · ${c.issue_type || "issue"} · resolution: ${c.resolution || "pending"}`
      );
      return notes.length ? notes.join("\n") : "No recent notes available.";
    }

    async function loadOptionalPanels() {
      const notes = await apiGet("/notes/recent");
      if (notes.ok) {
        setTool("notes", JSON.stringify(notes.data, null, 2));
        setStatus("notes", "done", "Notes loaded from backend.");
      } else {
        setTool("notes", deriveNotes(), "Derived");
      }

      const tasks = await apiGet("/tasks/open-summary");
      if (tasks.ok) {
        setTool("tasks", JSON.stringify(tasks.data, null, 2));
        setStatus("tasks", "done", "Tasks loaded from backend.");
      } else {
        setTool("tasks", deriveTasks().slice(0, 6).map(t => `${t.title} — ${t.detail}`).join("\n"), "Derived");
      }

      const calendar = await apiGet("/calendar/summary");
      if (calendar.ok) {
        setTool("calendar", JSON.stringify(calendar.data, null, 2));
        setStatus("calendar", "done", "Calendar loaded from backend.");
      } else {
        const ev = deriveCalendarEvents().slice(0,6);
        setTool("calendar", ev.length ? ev.map(e => `${e.date.toLocaleDateString()} — ${e.label}`).join("\n") : "No upcoming estimated events.", "Derived");
      }

      const manufacturer = await apiGet("/manufacturer/pending");
      if (manufacturer.ok) {
        const pending = manufacturer.data.pending_contacts || manufacturer.data.result || manufacturer.data.data || [];
        manufacturerPending = Array.isArray(pending) ? pending : [];
        setTool("manufacturer", manufacturerPending.length ? JSON.stringify(manufacturerPending.slice(0, 3), null, 2) : "No pending manufacturer escalations.");
        setStatus("manufacturer", "done", manufacturerPending.length ? "Manufacturer data loaded." : "No pending manufacturer escalations.");
      } else {
        setTool("manufacturer", "Manufacturer endpoint unavailable.", "Unavailable");
      }
    }

    async function runTracker() {
      if (!liveContext.lastProductName) {
        appendChatMessage("system", "Submit a complaint first so the tracker knows which product to follow.");
        pushActivity("Tracker skipped because no product context exists yet.");
        return;
      }

      setStatus("tracker", "running", `Running tracker for ${liveContext.lastProductName}...`);
      pushTrace(`Running tracker for ${liveContext.lastProductName}`, "RUN");
      pushActivity(`Tracker execution started for ${liveContext.lastProductName}`);

      const res = await apiPost("/tracker/run", { product_name: liveContext.lastProductName });
      if (res.ok && res.data.success) {
        setStatus("tracker", "done", "Tracker executed successfully.");
        setTool("tracker", JSON.stringify(res.data.result, null, 2));
        appendChatMessage("system", `Tracker ran for ${liveContext.lastProductName}.`);
        pushTrace(`Tracker completed for ${liveContext.lastProductName}`, "OK");
        pushActivity(`Tracker completed for ${liveContext.lastProductName}`);
      } else {
        setStatus("tracker", "error", "Tracker endpoint failed or is unavailable.");
        setTool("tracker", JSON.stringify(res.data || { error: "Tracker endpoint unavailable" }, null, 2), "Unavailable");
        pushTrace(`Tracker failed for ${liveContext.lastProductName}`, "ERR");
      }
      await loadAllData();
    }

    async function runLearning() {
      appendChatMessage("system", "Running learning agent...");
      pushTrace("Learning agent triggered", "RUN");
      pushActivity("Learning agent started");
      const res = await apiPost("/learning/run", {});
      if (res.ok && res.data.success) {
        appendChatMessage("system", "Learning agent finished successfully.");
        pushTrace("Learning agent completed", "OK");
        pushActivity("Learning agent completed");
      } else {
        appendChatMessage("system", "Learning endpoint unavailable or failed.");
        pushTrace("Learning endpoint unavailable", "ERR");
      }
    }

    async function submitComplaint() {
      const input = document.getElementById("complaintInput");
      const complaintText = input.value.trim();

      if (complaintText.length < 10) {
        appendChatMessage("system", "Please enter at least 10 characters.");
        return;
      }

      appendChatMessage("user", complaintText);

      setStatus("listener", "running", "Parsing complaint text...");
      setStatus("analyst", "pending", "Waiting for eligibility check.");
      setStatus("decision", "pending", "Waiting for decision.");
      setStatus("database", "pending", "Waiting for database write.");
      setStatus("customer", "pending", "Waiting for final response.");

      pushTrace("Complaint received in customer portal", "OK");
      pushTrace("Listener agent extracting fields", "RUN");
      pushActivity("Complaint submitted from customer portal");

      const res = await apiPost("/complaint", { complaint: complaintText });

      if (!(res.ok && res.data.success)) {
        setStatus("listener", "error", "Complaint submission failed.");
        setStatus("customer", "error", "No final response returned.");
        appendChatMessage("system", `Submission failed: ${(res.data && (res.data.detail || res.data.error)) || "Unknown error"}`);
        pushTrace("Complaint submission failed", "ERR");
        pushActivity("Complaint submission failed");
        return;
      }

      const body = res.data;
      const customer = body.customer_response || {};
      const steps = body.steps_completed || [];
      const decision = customer.decision || "unknown";
      const eta = customer.estimated_resolution_days ?? "unknown";

      liveContext.lastComplaintId = body.complaint_id || null;

      setStatus("listener", "done", "Complaint parsed successfully.");
      pushTrace("Listener extraction completed", "OK");
      pushTrace("Analyst checking policy eligibility", "RUN");
      pushActivity("Listener agent completed extraction");

      setStatus("analyst", steps.includes("analyst") ? "done" : "running", "Eligibility review completed.");
      pushTrace("Policy check completed", "OK");
      pushTrace("Decision agent generating response", "RUN");
      pushActivity("Analyst eligibility review completed");

      setStatus("decision", steps.includes("decision") ? "done" : "running", `Decision selected: ${decision}. ETA: ${eta} day(s).`);
      pushTrace(`Decision selected: ${decision}`, "OK");
      pushTrace("Writing case to database", "RUN");
      pushActivity(`Decision selected: ${decision}`);

      setStatus("database", steps.includes("database") ? "done" : "running", `Complaint logged with ID ${body.complaint_id || "unknown"}.`);
      pushTrace(`Database updated for complaint ${body.complaint_id || "unknown"}`, "OK");
      pushActivity(`Complaint logged with ID ${body.complaint_id || "unknown"}`);

      setStatus("customer", "done", "Customer response returned.");

      if (customer.acknowledgement) appendChatMessage("bot", customer.acknowledgement);
      if (customer.resolution) appendChatMessage("bot", customer.resolution);
      if (steps.length) appendChatMessage("system", `Completed stages: ${steps.join(", ")}`);

      pushTrace("Customer response returned to chat", "OK");
      pushActivity("Customer-facing response returned");

      await loadAllData();

      const found = complaintsData.find(c => c.complaint_id === body.complaint_id);
      if (found) liveContext.lastProductName = found.product_name || null;

      await loadOptionalPanels();

      if (liveContext.lastProductName) {
        setStatus("tracker", "pending", `Tracker ready for ${liveContext.lastProductName}.`);
        setTool("tracker", `Tracker ready for product: ${liveContext.lastProductName}\nUse "Run Tracker" to execute follow-up.`);
      }

      if (manufacturerPending.length) {
        const related = manufacturerPending.find(x => x.product_name === liveContext.lastProductName) || manufacturerPending[0];
        if (related) {
          setStatus("manufacturer", "done", `Manufacturer record found for ${related.product_name}. Email sent: ${related.email_sent ? "yes" : "no"}.`);
          setTool("manufacturer", JSON.stringify(related, null, 2));
          pushTrace(`Manufacturer state checked for ${related.product_name}`, "OK");
          pushActivity(`Manufacturer state loaded for ${related.product_name}`);
        }
      } else {
        setStatus("manufacturer", "done", "No manufacturer escalation triggered.");
        pushTrace("No manufacturer escalation triggered", "OK");
      }

      setStatus("notes", "pending", "Refreshing notes panel...");
      setStatus("tasks", "pending", "Refreshing tasks panel...");
      setStatus("calendar", "pending", "Refreshing calendar panel...");
    }

    async function loadAllData() {
      const dashboard = await apiGet("/dashboard");
      const complaints = await apiGet("/complaints");
      const products = await apiGet("/products");
      const manufacturer = await apiGet("/manufacturer/pending");

      if (dashboard.ok) {
        dashboardData = dashboard.data.data || dashboard.data || {};
        document.getElementById("apiStatus").textContent = `API: connected → ${API_BASE}`;
      } else {
        dashboardData = {};
        document.getElementById("apiStatus").textContent = `API: dashboard failed → ${API_BASE}`;
      }

      complaintsData = complaints.ok ? (complaints.data.complaints || complaints.data.data || []) : [];
      productsData = products.ok ? (products.data.products || products.data.product_stats || products.data.data || []) : [];
      manufacturerPending = manufacturer.ok ? (manufacturer.data.pending_contacts || manufacturer.data.data || []) : [];

      setLastUpdated();
      renderKPIs();
      makeBarList("resolutionBars", dashboardData.resolution_breakdown || {});
      renderDonut(dashboardData.issue_breakdown || {});
      populateFilters();
      renderComplaints();
      renderProducts();
      renderKanban();
      renderCalendar();
      renderTrace();
      renderActivity();
      renderStatuses();
      renderTools();
    }

    document.querySelectorAll(".nav-btn").forEach(btn => {
      btn.addEventListener("click", () => activatePage(btn.dataset.page));
    });

    document.getElementById("refreshBtn").addEventListener("click", async () => {
      await loadAllData();
      await loadOptionalPanels();
      pushActivity("Dashboard refreshed");
    });

    document.getElementById("submitComplaintBtn").addEventListener("click", submitComplaint);
    document.getElementById("resetBtn").addEventListener("click", resetChat);
    document.getElementById("trackerBtn").addEventListener("click", runTracker);
    document.getElementById("learningBtn").addEventListener("click", runLearning);

    document.getElementById("sampleComplaint").addEventListener("change", e => {
      if (e.target.value) document.getElementById("complaintInput").value = e.target.value;
    });

    ["filterProduct", "filterResolution", "filterUrgency", "filterIssue"].forEach(id => {
      document.getElementById(id).addEventListener("change", renderComplaints);
    });

    initSystemPanels();
    resetChat();
    loadAllData().then(loadOptionalPanels);
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def dashboard_home():
    return HTMLResponse(HTML.replace("__API_BASE__", API_BASE))

@app.get("/health")
def health():
    return JSONResponse({"status": "healthy", "api_base": API_BASE})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=False)
