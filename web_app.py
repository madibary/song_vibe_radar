import asyncio
import json
import logging
import os
import queue
import threading
from typing import cast

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, StreamingResponse
from starlette.routing import Route

load_dotenv()
logging.basicConfig(level=logging.WARNING)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Song Radar</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f4f8;color:#1a1a2e;min-height:100vh}
.header{text-align:center;padding:3rem 1rem 1.5rem}
.logo{font-size:2.8rem;display:block;margin-bottom:.5rem;animation:pulse 3s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
h1{font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#db2777);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.02em}
.subtitle{color:#9090a8;margin-top:.4rem;font-size:.95rem}
.search-wrap{max-width:520px;margin:1.5rem auto 0;padding:0 1rem}
.card{background:#ffffff;border:1px solid #e5e3ef;border-radius:16px;padding:1.5rem;box-shadow:0 2px 12px #7c3aed0d}
.inputs{display:flex;flex-direction:column;gap:.65rem;margin-bottom:.9rem}
input{width:100%;padding:.8rem 1.1rem;background:#faf9fc;border:1px solid #ddd9ea;border-radius:10px;color:#1a1a2e;font-size:.95rem;outline:none;transition:border-color .2s,box-shadow .2s}
input:focus{border-color:#7c3aed;box-shadow:0 0 0 3px #7c3aed18}
input::placeholder{color:#b8b4cc}
button{width:100%;padding:.85rem;background:linear-gradient(135deg,#7c3aed,#db2777);border:none;border-radius:10px;color:#fff;font-size:.95rem;font-weight:700;cursor:pointer;transition:opacity .2s,transform .1s;letter-spacing:.02em}
button:hover{opacity:.88}
button:active{transform:scale(.98)}
button:disabled{opacity:.45;cursor:not-allowed}

/* progress */
.progress-wrap{max-width:520px;margin:1.25rem auto 0;padding:0 1rem;display:none}
.progress-wrap.show{display:block}
.steps{display:flex;flex-direction:column;gap:0}
.step{display:flex;align-items:center;gap:.85rem;padding:.55rem 0;color:#c5c0d8;font-size:.875rem;transition:color .3s}
.step.active{color:#7c3aed}
.step.done{color:#a09cb8}
.dot{width:7px;height:7px;border-radius:50%;background:#e5e3ef;flex-shrink:0;transition:background .3s,box-shadow .3s}
.step.active .dot{background:#7c3aed;box-shadow:0 0 8px #7c3aed55;animation:blink 1.2s ease-in-out infinite}
.step.done .dot{background:#b8b4cc}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* results */
.results-wrap{max-width:680px;margin:1.5rem auto 4rem;padding:0 1rem;display:none}
.results-wrap.show{display:block}
.ref-card{margin-bottom:1.25rem}
.chip{display:inline-block;font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#7c3aed;background:#7c3aed12;padding:.2rem .55rem;border-radius:5px;margin-bottom:.6rem}
.ref-name{font-size:1.35rem;font-weight:700;color:#1a1a2e}
.ref-artist{color:#9090a8;margin-top:.15rem;font-size:.9rem}
.vibe-quote{color:#6b6880;margin-top:.85rem;font-style:italic;line-height:1.65;font-size:.875rem;border-left:2px solid #e5e3ef;padding-left:.85rem}
.recs-label{font-size:.8rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#9090a8;margin-bottom:.85rem}
.song-list{display:flex;flex-direction:column;gap:.65rem}
.song-card{display:flex;align-items:flex-start;gap:1rem;transition:border-color .2s}
.song-card:hover{border-color:#ddd9ea}
.rank{font-size:1.4rem;font-weight:800;color:#ddd9ea;width:2rem;flex-shrink:0;text-align:right;line-height:1.2;margin-top:.05rem}
.rank.gold{background:linear-gradient(135deg,#db2777,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.info{flex:1}
.song-name{font-weight:600;font-size:.95rem;color:#1a1a2e}
.best-badge{display:inline-block;font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:linear-gradient(135deg,#7c3aed,#db2777);color:#fff;padding:.15rem .45rem;border-radius:4px;margin-left:.45rem;vertical-align:middle}
.song-artist{color:#9090a8;font-size:.825rem;margin-top:.1rem}
.song-vibe{color:#6b6880;font-size:.8rem;margin-top:.45rem;line-height:1.55}
.bar-row{display:flex;align-items:center;gap:.5rem;margin-top:.5rem}
.bar{flex:1;height:3px;background:#e5e3ef;border-radius:2px;overflow:hidden}
.bar-fill{height:100%;background:linear-gradient(90deg,#7c3aed,#db2777);border-radius:2px;width:0;transition:width 1.2s cubic-bezier(.22,1,.36,1)}
.bar-pct{font-size:.7rem;color:#7c3aed;font-weight:700;min-width:2.5rem;text-align:right}
.err{color:#dc2626;text-align:center;padding:1.5rem;font-size:.9rem}
</style>
</head>
<body>

<div class="header">
  <span class="logo">🎵</span>
  <h1>Song Radar</h1>
  <p class="subtitle">Find songs with the same vibe</p>
</div>

<div class="search-wrap">
  <div class="card">
    <div class="inputs">
      <input id="track" type="text" placeholder="Track name" autocomplete="off">
      <input id="artist" type="text" placeholder="Artist name" autocomplete="off">
    </div>
    <button id="btn" onclick="doSearch()">Find my vibe →</button>
  </div>
</div>

<div class="progress-wrap card" id="progress">
  <div class="steps">
    <div class="step" id="s-validate"><span class="dot"></span>Validating song</div>
    <div class="step" id="s-enrich"><span class="dot"></span>Gathering song information</div>
    <div class="step" id="s-vibe"><span class="dot"></span>Generating vibe description</div>
    <div class="step" id="s-reflect"><span class="dot"></span>Evaluating description quality</div>
    <div class="step" id="s-recommend"><span class="dot"></span>Finding similar songs</div>
    <div class="step" id="s-worker"><span class="dot"></span>Analysing recommendation vibes</div>
  </div>
</div>

<div class="results-wrap" id="results"></div>

<script>
const NODE_STEPS = {
  validate_reference_song: 's-validate',
  enrich_reference_song:   's-enrich',
  analyze_vibe:            's-vibe',
  reflect:                 's-reflect',
  get_song_recommendations:'s-recommend',
  music_worker:            's-worker',
};

function setActive(stepId) {
  document.querySelectorAll('.step.active').forEach(el => {
    el.classList.remove('active'); el.classList.add('done');
  });
  const el = document.getElementById(stepId);
  if (el) el.classList.add('active');
}

function allDone() {
  document.querySelectorAll('.step.active').forEach(el => {
    el.classList.remove('active'); el.classList.add('done');
  });
}

function esc(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderResults(state) {
  const el = document.getElementById('results');
  if (state.error) {
    el.innerHTML = `<div class="err">❌ ${esc(state.error)}</div>`;
    el.classList.add('show');
    return;
  }
  const ref   = state.reference_track || {};
  const songs = state.sorted_songs   || [];
  const best  = state.best_match;

  let h = `
    <div class="card ref-card">
      <div class="chip">Reference track</div>
      <div class="ref-name">${esc(ref.name)}</div>
      <div class="ref-artist">by ${esc(ref.artist)}</div>
      ${ref.vibe_description ? `<div class="vibe-quote">${esc(ref.vibe_description)}</div>` : ''}
    </div>
    <div class="recs-label">Top recommendations</div>
    <div class="song-list">
  `;

  songs.forEach((s, i) => {
    const pct   = typeof s.score === 'number' ? Math.round(s.score * 100) : null;
    const isTop = i === 0;
    const isBest = best && s.name === best.name && s.artist === best.artist;
    h += `
      <div class="card song-card">
        <div class="rank ${isTop ? 'gold' : ''}">${i + 1}</div>
        <div class="info">
          <div class="song-name">${esc(s.name)}${isBest ? '<span class="best-badge">Best match</span>':''}</div>
          <div class="song-artist">${esc(s.artist)}</div>
          ${s.vibe_description ? `<div class="song-vibe">${esc(s.vibe_description)}</div>` : ''}
          ${pct !== null ? `
            <div class="bar-row">
              <div class="bar"><div class="bar-fill" data-pct="${pct}"></div></div>
              <div class="bar-pct">${pct}%</div>
            </div>` : ''}
        </div>
      </div>`;
  });

  h += '</div>';
  el.innerHTML = h;
  el.classList.add('show');

  // animate bars after paint
  requestAnimationFrame(() => requestAnimationFrame(() => {
    el.querySelectorAll('.bar-fill').forEach(b => {
      b.style.width = b.dataset.pct + '%';
    });
  }));
}

async function doSearch() {
  const track  = document.getElementById('track').value.trim();
  const artist = document.getElementById('artist').value.trim();
  if (!track || !artist) return;

  const btn = document.getElementById('btn');
  btn.disabled = true; btn.textContent = 'Scanning…';

  // reset
  document.querySelectorAll('.step').forEach(s => s.className = 'step');
  const prog = document.getElementById('progress');
  const res  = document.getElementById('results');
  prog.classList.add('show');
  res.classList.remove('show'); res.innerHTML = '';

  try {
    const resp = await fetch('/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({track, artist})
    });

    const reader  = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += decoder.decode(value, {stream: true});
      const parts = buf.split('\\n\\n');
      buf = parts.pop();
      for (const part of parts) {
        if (!part.startsWith('data: ')) continue;
        const msg = JSON.parse(part.slice(6));
        if (msg.type === 'progress') {
          const id = NODE_STEPS[msg.node];
          if (id) setActive(id);
        } else if (msg.type === 'done') {
          allDone();
          renderResults(msg.state);
        } else if (msg.type === 'error') {
          res.innerHTML = `<div class="err">❌ ${esc(msg.message)}</div>`;
          res.classList.add('show');
        }
      }
    }
  } catch (e) {
    document.getElementById('results').innerHTML = `<div class="err">❌ ${esc(e.message)}</div>`;
    document.getElementById('results').classList.add('show');
  }

  btn.disabled = false; btn.textContent = 'Find my vibe →';
}

document.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
</script>
</body>
</html>
"""


def _safe_float(val):
    try:
        return float(val)
    except Exception:
        return None


def _serialize(state: dict) -> dict:
    ref = state.get("reference_track") or {}
    songs = state.get("sorted_songs") or []
    best = state.get("best_match")
    return {
        "reference_track": {
            "name": ref.get("name"),
            "artist": ref.get("artist"),
            "vibe_description": ref.get("vibe_description"),
        },
        "sorted_songs": [
            {
                "name": s.get("name"),
                "artist": s.get("artist"),
                "vibe_description": s.get("vibe_description"),
                "score": _safe_float(s.get("score")),
            }
            for s in songs
        ],
        "best_match": {"name": best.get("name"), "artist": best.get("artist")} if best else None,
        "error": state.get("error"),
    }


async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse(HTML)


async def search(request: Request) -> StreamingResponse:
    data = await request.json()
    track_name = (data.get("track") or "").strip()
    artist_name = (data.get("artist") or "").strip()

    async def stream():
        from state.agent_state import AgentState
        from graphs.main_graph import graph

        q: queue.Queue = queue.Queue()

        def run():
            initial: dict = {
                "reference_track": {"name": track_name, "artist": artist_name},
                "reference_iterations": 0,
                "reference_feedback": "",
            }
            accumulated = initial.copy()
            try:
                for updates in graph.stream(cast(AgentState, initial), stream_mode="updates"):
                    for node_name, update in updates.items():
                        if update is not None:
                            accumulated.update(update)
                        q.put(("progress", node_name, None))
                q.put(("done", None, accumulated))
            except Exception as exc:
                q.put(("error", str(exc), None))

        threading.Thread(target=run, daemon=True).start()

        while True:
            kind, a, b = await asyncio.to_thread(q.get)
            if kind == "progress":
                yield f"data: {json.dumps({'type': 'progress', 'node': a})}\n\n"
            elif kind == "done":
                yield f"data: {json.dumps({'type': 'done', 'state': _serialize(b)})}\n\n"
                break
            elif kind == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': a})}\n\n"
                break

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app = Starlette(routes=[
    Route("/", homepage),
    Route("/search", search, methods=["POST"]),
])
