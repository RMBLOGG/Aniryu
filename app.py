from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)
BASE_URL = "https://www.sankavollerei.com"

def fetch(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "data": None}

# Pages
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

# API proxy
@app.route("/api/home")
def api_home(): return jsonify(fetch("/anime/home"))

@app.route("/api/schedule")
def api_schedule(): return jsonify(fetch("/anime/schedule"))

@app.route("/api/ongoing")
def api_ongoing(): return jsonify(fetch("/anime/ongoing-anime", {"page": request.args.get("page", 1)}))

@app.route("/api/completed")
def api_completed(): return jsonify(fetch("/anime/complete-anime", {"page": request.args.get("page", 1)}))

@app.route("/api/anime/<slug>")
def api_anime(slug): return jsonify(fetch(f"/anime/anime/{slug}"))

@app.route("/api/episode/<slug>")
def api_episode(slug): return jsonify(fetch(f"/anime/episode/{slug}"))

@app.route("/api/genre")
def api_genre(): return jsonify(fetch("/anime/genre"))

@app.route("/api/genre/<slug>")
def api_genre_detail(slug): return jsonify(fetch(f"/anime/genre/{slug}", {"page": request.args.get("page", 1)}))

@app.route("/api/search/<keyword>")
def api_search(keyword): return jsonify(fetch(f"/anime/search/{keyword}"))

@app.route("/api/batch/<slug>")
def api_batch(slug): return jsonify(fetch(f"/anime/batch/{slug}"))

@app.route("/api/server/<server_id>")
def api_server(server_id): return jsonify(fetch(f"/anime/server/{server_id}"))

if __name__ == "__main__":
    app.run(debug=True)
