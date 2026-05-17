from flask import Flask, render_template, jsonify, request, Response, stream_with_context
import requests, os, json, queue, threading, hmac, hashlib

app = Flask(__name__)

BASE_URL = "https://www.sankavollerei.com"

# ── Supabase config ──────────────────────────────────────────────────────────
SUPABASE_URL      = "https://mafnnqttvkdgqqxczqyt.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hZm5ucXR0dmtkZ3FxeGN6cXl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4NzQyMDEsImV4cCI6MjA4NzQ1MDIwMX0.YRh1oWVKnn4tyQNRbcPhlSyvr7V_1LseWN7VjcImb-Y"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hZm5ucXR0dmtkZ3FxeGN6cXl0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg3NDIwMSwiZXhwIjoyMDg3NDUwMjAxfQ.2I06TOtfOJErlZPzuWdOFofII_agGgzZzKClqLo6EMg"

# Saweria webhook secret — set di Vercel env: SAWERIA_SECRET
SAWERIA_SECRET = ""

# SSE broadcast queues
_sse_clients = []
_sse_lock = threading.Lock()

def _broadcast(data):
    msg = "data: " + json.dumps(data) + "\n\n"
    with _sse_lock:
        dead = []
        for q in _sse_clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _sse_clients.remove(q)

# ── Supabase helpers ─────────────────────────────────────────────────────────
def _supa_headers(use_service=False):
    key = SUPABASE_SERVICE_KEY if (use_service and SUPABASE_SERVICE_KEY) else SUPABASE_ANON_KEY
    return {
        "apikey": key,
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def supa_insert(table, data):
    r = requests.post(
        SUPABASE_URL + "/rest/v1/" + table,
        headers=_supa_headers(use_service=True),
        json=data, timeout=8,
    )
    return r.json()

def supa_select(table, query=""):
    r = requests.get(
        SUPABASE_URL + "/rest/v1/" + table + ("?" + query if query else ""),
        headers=_supa_headers(),
        timeout=8,
    )
    return r.json()

# ── Anime API helper ─────────────────────────────────────────────────────────
def fetch(path, params=None):
    try:
        r = requests.get(BASE_URL + path, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "data": None}

# ════════════════════════════════════════════════════════════════════════════
#  PAGES
# ════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index(): return render_template("index.html")

@app.route("/anime/<slug>")
def anime_detail(slug): return render_template("detail.html", slug=slug)

@app.route("/watch/<slug>")
def watch(slug): return render_template("watch.html", slug=slug)

@app.route("/genre")
def genre_page(): return render_template("genre.html")

@app.route("/genre/<slug>")
def genre_detail(slug): return render_template("genre_detail.html", slug=slug)

@app.route("/schedule")
def schedule_page(): return render_template("schedule.html")

@app.route("/search")
def search_page(): return render_template("search.html")

@app.route("/ongoing")
def ongoing_page(): return render_template("ongoing.html")

@app.route("/completed")
def completed_page(): return render_template("completed.html")

@app.route("/faq")
def faq_page(): return render_template("faq.html")

@app.route("/tentang")
def tentang_page(): return render_template("tentang.html")

@app.route("/bookmark")
def bookmark_page(): return render_template("bookmark.html")

@app.route("/donasi")
def donasi_page(): return render_template("donasi.html")

# ════════════════════════════════════════════════════════════════════════════
#  ANIME API PROXY
# ════════════════════════════════════════════════════════════════════════════
@app.route("/api/home")
def api_home(): return jsonify(fetch("/anime/home"))

@app.route("/api/schedule")
def api_schedule(): return jsonify(fetch("/anime/schedule"))

@app.route("/api/ongoing")
def api_ongoing(): return jsonify(fetch("/anime/ongoing-anime", {"page": request.args.get("page", 1)}))

@app.route("/api/completed")
def api_completed(): return jsonify(fetch("/anime/complete-anime", {"page": request.args.get("page", 1)}))

@app.route("/api/anime/<slug>")
def api_anime(slug): return jsonify(fetch("/anime/anime/" + slug))

@app.route("/api/episode/<slug>")
def api_episode(slug): return jsonify(fetch("/anime/episode/" + slug))

@app.route("/api/genre")
def api_genre(): return jsonify(fetch("/anime/genre"))

@app.route("/api/genre/<slug>")
def api_genre_detail(slug): return jsonify(fetch("/anime/genre/" + slug, {"page": request.args.get("page", 1)}))

@app.route("/api/search/<keyword>")
def api_search(keyword): return jsonify(fetch("/anime/search/" + keyword))

@app.route("/api/batch/<slug>")
def api_batch(slug): return jsonify(fetch("/anime/batch/" + slug))

@app.route("/api/server/<server_id>")
def api_server(server_id): return jsonify(fetch("/anime/server/" + server_id))

# ════════════════════════════════════════════════════════════════════════════
#  DONASI API
# ════════════════════════════════════════════════════════════════════════════
@app.route("/api/donasi/leaderboard")
def api_leaderboard():
    try:
        rows = supa_select("aniryu", "select=donatur,amount&order=created_at.desc&limit=500")
        totals = {}
        for row in (rows or []):
            name = row.get("donatur") or "Anonim"
            totals[name] = totals.get(name, 0) + (row.get("amount") or 0)
        ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
        return jsonify([{"donatur": k, "total": v} for k, v in ranked])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/donasi/target")
def api_target():
    try:
        target_rows = supa_select("aniryu_target", "select=judul,target_amount&limit=1")
        donasi_rows = supa_select("aniryu", "select=amount")
        target_amount = 500000
        judul = "Target Donasi"
        if target_rows and isinstance(target_rows, list) and len(target_rows) > 0:
            target_amount = target_rows[0].get("target_amount", 500000)
            judul = target_rows[0].get("judul", "Target Donasi")
        terkumpul = sum((r.get("amount") or 0) for r in (donasi_rows or []))
        persen = min(round(terkumpul / target_amount * 100, 1), 100) if target_amount > 0 else 0
        return jsonify({"judul": judul, "target": target_amount, "terkumpul": terkumpul, "persen": persen})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/donasi/recent")
def api_recent():
    try:
        rows = supa_select("aniryu", "select=donatur,amount,pesan,created_at&order=created_at.desc&limit=5")
        return jsonify(rows or [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════════════════════════
#  SAWERIA WEBHOOK
# ════════════════════════════════════════════════════════════════════════════
@app.route("/api/saweria/webhook", methods=["POST"])
def saweria_webhook():
    payload = request.get_json(silent=True) or {}

    # Saweria payload: donator_name, amount_raw
    donatur = payload.get("donator_name") or payload.get("donatur_name") or payload.get("donor_name") or "Anonim"
    try:
        amount = int(payload.get("amount_raw") or payload.get("amount") or 0)
    except (ValueError, TypeError):
        amount = 0
    pesan = payload.get("message") or payload.get("pesan") or ""

    if amount <= 0:
        return jsonify({"status": "ignored"}), 200

    supa_insert("aniryu", {"donatur": donatur, "amount": amount, "pesan": pesan})
    _broadcast({"event": "donasi_baru", "donatur": donatur, "amount": amount, "pesan": pesan})

    return jsonify({"status": "ok"}), 200

# ════════════════════════════════════════════════════════════════════════════
#  SSE — real-time update tanpa refresh
# ════════════════════════════════════════════════════════════════════════════
@app.route("/api/donasi/stream")
def donasi_stream():
    q = queue.Queue(maxsize=10)
    with _sse_lock:
        _sse_clients.append(q)

    def generate():
        yield "data: {\"event\":\"connected\"}\n\n"
        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield msg
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )

if __name__ == "__main__":
    app.run(debug=True)
