import asyncio
import json
import logging
import os
import queue
import re
import threading
from typing import cast

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, StreamingResponse
from starlette.routing import Route

load_dotenv()
logging.basicConfig(level=logging.WARNING)

from graphs.main_graph import graph as _graph
from state.agent_state import AgentState as _AgentState
from helpers.rate_limit import check_ip_limit, check_global_budget

_search_semaphore = asyncio.Semaphore(3)

_spotify_client = None


def _get_spotify() -> spotipy.Spotify:
    global _spotify_client
    if _spotify_client is None:
        _spotify_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        ))
    return _spotify_client


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _resolve_spotify_url(url: str) -> tuple[str, str]:
    match = re.search(r'spotify\.com/track/([A-Za-z0-9]+)', url)
    if not match:
        raise ValueError("Invalid Spotify track URL")
    track_id = match.group(1)
    track = _get_spotify().track(track_id)
    if not track:
        raise ValueError("Track not found on Spotify")
    name = track["name"]
    artist = track["artists"][0]["name"]
    return name, artist

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Song Radar</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f4ff;color:#0f172a;min-height:100vh}
.header{text-align:center;padding:3rem 1rem 1.5rem}
.logo{font-size:2.8rem;display:block;margin-bottom:.5rem;animation:float 3s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0) rotate(-5deg)}50%{transform:translateY(-6px) rotate(5deg)}}
h1{font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,#1e3a8a,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.02em}
.subtitle{color:#1d4ed8;margin-top:.4rem;font-size:1.1rem;letter-spacing:.02em}
.search-wrap{max-width:520px;margin:1.5rem auto 1rem;padding:0}
.card{background:rgba(255,255,255,0.9);border:1px solid #bfdbfe;border-radius:16px;padding:1.5rem;box-shadow:0 2px 16px #1e40af0e}
.inputs{display:flex;flex-direction:column;gap:.65rem;margin-bottom:.9rem}
input{width:100%;padding:.8rem 1.1rem;background:#f8fafc;border:1px solid #93c5fd;border-radius:10px;color:#0f172a;font-size:.95rem;outline:none;transition:border-color .2s,box-shadow .2s}
input:focus{border-color:#1e40af;box-shadow:0 0 0 3px #1e40af18}
input::placeholder{color:#60a5fa}
button{width:100%;padding:.85rem;background:linear-gradient(135deg,#1e3a8a,#1d4ed8);border:none;border-radius:10px;color:#fff;font-size:.95rem;font-weight:700;cursor:pointer;transition:opacity .2s,transform .1s;letter-spacing:.04em}
button:hover{opacity:.88}
button:active{transform:scale(.98)}
button:disabled{opacity:.45;cursor:not-allowed}

/* progress */
.progress-wrap{max-width:520px;margin:1.25rem auto 0;padding:0 1rem;display:none}
.progress-wrap.show{display:block}
.steps{display:flex;flex-direction:column;gap:0}
.step{display:flex;align-items:center;gap:.85rem;padding:.55rem 0;color:#93c5fd;font-size:.875rem;transition:color .3s}
.step.active{color:#1e40af}
.step.done{color:#3b82f6}
.dot{width:7px;height:7px;border-radius:50%;background:#dbeafe;flex-shrink:0;transition:background .3s,box-shadow .3s}
.step.active .dot{background:#1e40af;box-shadow:0 0 8px #1e40af55;animation:blink 1.2s ease-in-out infinite}
.step.done .dot{background:#60a5fa}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* results */
.results-wrap{max-width:680px;margin:1.5rem auto 4rem;padding:0 1rem;display:none}
.results-wrap.show{display:block}
.ref-card{margin-bottom:1.25rem}
.chip{display:inline-block;font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#1e40af;background:#dbeafe;padding:.2rem .55rem;border-radius:5px;margin-bottom:.6rem}
.ref-name{font-size:1.35rem;font-weight:700;color:#0f172a}
.ref-artist{color:#3b82f6;margin-top:.15rem;font-size:.9rem}
.vibe-quote{color:#1e3a8a;margin-top:.85rem;font-style:italic;line-height:1.65;font-size:.875rem;border-left:2px solid #bfdbfe;padding-left:.85rem}
.recs-label{font-size:.8rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#60a5fa;margin-bottom:.85rem}
.song-list{display:flex;flex-direction:column;gap:.65rem}
.song-card{display:flex;align-items:flex-start;gap:1rem;transition:border-color .2s}
.song-card:hover{border-color:#93c5fd}
.rank{font-size:1.4rem;font-weight:800;color:#bfdbfe;width:2rem;flex-shrink:0;text-align:right;line-height:1.2;margin-top:.05rem}
.rank.gold{background:linear-gradient(135deg,#1e3a8a,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.info{flex:1}
.song-name{font-weight:600;font-size:.95rem;color:#0f172a}
.best-badge{display:inline-block;font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:linear-gradient(135deg,#1e3a8a,#2563eb);color:#fff;padding:.15rem .45rem;border-radius:4px;margin-left:.45rem;vertical-align:middle}
.song-artist{color:#3b82f6;font-size:.825rem;margin-top:.1rem}
.song-vibe{color:#1e3a8a;font-size:.8rem;margin-top:.45rem;line-height:1.55}
.bar-row{display:flex;align-items:center;gap:.5rem;margin-top:.5rem}
.bar{flex:1;height:3px;background:#dbeafe;border-radius:2px;overflow:hidden}
.bar-fill{height:100%;background:linear-gradient(90deg,#1e3a8a,#2563eb);border-radius:2px;width:0;transition:width 1.2s cubic-bezier(.22,1,.36,1)}
.bar-pct{font-size:.7rem;color:#1e40af;font-weight:700;min-width:2.5rem;text-align:right}
.err{color:#dc2626;text-align:center;padding:1.5rem;font-size:.9rem}
.spotify-link{display:inline-block;margin-top:.4rem;font-size:.75rem;color:#1e40af;font-weight:600;text-decoration:none;opacity:.8}
.spotify-link:hover{opacity:1;text-decoration:underline}
</style>
</head>
<body>

<div class="header">
  <span class="logo">🐚</span>
  <h1>Song Radar</h1>
  <p class="subtitle">🌊 find songs with the same vibe 🫧</p>
</div>

<div class="search-wrap">
  <div class="card">
    <div class="inputs">
      <input id="spotify_url" type="text" placeholder="🎵 Paste a Spotify track link" autocomplete="off" oninput="onUrlInput()">
    </div>
    <div id="track-preview" style="display:none;margin-bottom:.5rem;padding:.55rem .85rem;background:#dbeafe;border-radius:8px;font-size:.875rem;color:#1e3a8a;font-weight:600"></div>
    <button id="btn" onclick="doSearch()">🐚 Find my vibe</button>
  </div>
</div>

<div class="progress-wrap card" id="progress">
  <div class="steps">
    <div class="step" id="s-enrich"><span class="dot"></span>🌊 Gathering song information</div>
    <div class="step" id="s-vibe"><span class="dot"></span>🐚 Generating vibe description</div>
    <!--EVALUATION_STEP-->
    <div class="step" id="s-recommend"><span class="dot"></span>✨ Finding similar songs</div>
    <div class="step" id="s-worker"><span class="dot"></span>🫧 Analysing recommendation vibes</div>
  </div>
</div>

<div class="results-wrap" id="results"></div>

<script>
const NODE_STEPS = {
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
          <a class="spotify-link" href="https://open.spotify.com/search/${encodeURIComponent(s.name + ' ' + s.artist)}" target="_blank">▶ Listen on Spotify</a>
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

let _resolveTimer = null;
function onUrlInput() {
  const url = document.getElementById('spotify_url').value.trim();
  const preview = document.getElementById('track-preview');
  preview.style.display = 'none';
  clearTimeout(_resolveTimer);
  if (!url.includes('spotify.com/track/')) return;
  _resolveTimer = setTimeout(async () => {
    try {
      const res = await fetch('/resolve-track', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({spotify_url: url})
      });
      const data = await res.json();
      if (data.name) {
        preview.textContent = '🎵 ' + data.name + ' · ' + data.artist;
        preview.style.display = 'block';
      }
    } catch(e) {}
  }, 400);
}

async function doSearch() {
  const spotify_url = document.getElementById('spotify_url').value.trim();
  if (!spotify_url) return;

  const res = document.getElementById('results');

  if (!spotify_url.includes('spotify.com/track/')) {
    res.innerHTML = `<div class="err">❌ Please paste a valid Spotify track link (e.g. open.spotify.com/track/…)</div>`;
    res.classList.add('show');
    return;
  }

  const btn = document.getElementById('btn');
  btn.disabled = true; btn.textContent = 'Scanning…';

  // reset
  document.querySelectorAll('.step').forEach(s => s.className = 'step');
  const prog = document.getElementById('progress');
  prog.classList.add('show');
  res.classList.remove('show'); res.innerHTML = '';

  try {
    const resp = await fetch('/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({spotify_url})
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


_EVALUATION_STEP = '<div class="step" id="s-reflect"><span class="dot"></span>🦪 Evaluating description quality</div>'

async def resolve_track(request: Request):
    from starlette.responses import JSONResponse
    data = await request.json()
    try:
        name, artist = _resolve_spotify_url((data.get("spotify_url") or "").strip())
        return JSONResponse({"name": name, "artist": artist})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def health(request: Request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok"})


async def homepage(request: Request) -> HTMLResponse:
    evaluation_enabled = os.getenv("EVALUATION_ENABLED", "").lower() == "true"
    html = HTML.replace("<!--EVALUATION_STEP-->", _EVALUATION_STEP if evaluation_enabled else "")
    return HTMLResponse(html)


async def search(request: Request) -> StreamingResponse:
    def _sse_error(msg: str) -> StreamingResponse:
        async def _body():
            yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
        return StreamingResponse(_body(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    if not check_global_budget():
        return _sse_error("The service is temporarily unavailable. Please try again later.")

    if not check_ip_limit(_client_ip(request)):
        return _sse_error("Too many requests. Please wait a while before trying again.")

    data = await request.json()
    try:
        track_name, artist_name = _resolve_spotify_url((data.get("spotify_url") or "").strip())
    except Exception as e:
        return _sse_error(str(e))

    async def stream():
        async with _search_semaphore:
            q: queue.Queue = queue.Queue()

            def run():
                initial: dict = {
                    "reference_track": {"name": track_name, "artist": artist_name},
                    "reference_iterations": 0,
                    "reference_feedback": "",
                }
                accumulated = initial.copy()
                try:
                    for updates in _graph.stream(cast(_AgentState, initial), stream_mode="updates"):
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
    Route("/health", health),
    Route("/", homepage),
    Route("/resolve-track", resolve_track, methods=["POST"]),
    Route("/search", search, methods=["POST"]),
])
