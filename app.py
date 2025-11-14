
import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

app = Flask(__name__)

# DB file next to this module
DB_PATH = Path(__file__).parent / "posts.db"

# Seed data used only when DB is empty on first run
SEED_POSTS = [
    {
        "title": "30 Fun and Fascinating Dog Facts",
        "url": "https://www.akc.org/expert-advice/lifestyle/dog-facts/",
        "score": 10,
    },
    {
        "title": "Why Do Dogs Tilt Their Heads?",
        "url": "https://www.sciencefocus.com/nature/why-do-dogs-tilt-their-head-when-you-speak-to-them",
        "score": 5,
    },
    {
        "title": "r/dogs — top posts",
        "url": "https://www.reddit.com/r/dogs/",
        "score": 3,
    },
    {
        "title": "Basic Dog Training Guide",
        "url": "https://www.animalhumanesociety.org/resource/how-get-most-out-training-your-dog",
        "score": 2,
    },
    {
        "title": "The Dogist (photo stories)",
        "url": "https://thedogist.com/",
        "score": 1,
    },
]


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db_and_seed():
    """Create posts table if missing and seed from SEED_POSTS if empty."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            score INTEGER NOT NULL,
            hidden INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(1) FROM posts")
    (count,) = cur.fetchone()
    if count == 0:
        for p in SEED_POSTS:
            cur.execute("INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, ?, 0)", (p["title"], p["url"], p["score"]))
        conn.commit()
    conn.close()


@app.before_request
def ensure_db():
    init_db_and_seed()


@app.teardown_appcontext
def teardown_db(exc):
    close_db()


@app.get("/")
def homepage():
    db = get_db()
    visible = db.execute("SELECT id, title, url, score, hidden, created_at FROM posts WHERE hidden = 0 ORDER BY score DESC").fetchall()
    hidden = db.execute("SELECT id, title, url, score, hidden, created_at FROM posts WHERE hidden = 1 ORDER BY score DESC").fetchall()
    # convert Row objects to dict for templates
    visible_links = [dict(r) for r in visible]
    hidden_links = [dict(r) for r in hidden]
    return render_template("index.html", links=visible_links, hidden_posts=hidden_links)


@app.post('/upvote/<int:link_id>')
def upvote(link_id: int):
    db = get_db()
    db.execute("UPDATE posts SET score = score + 1 WHERE id = ?", (link_id,))
    db.commit()
    return redirect(url_for("homepage"))


@app.post('/downvote/<int:link_id>')
def downvote(link_id: int):
    db = get_db()
    db.execute("UPDATE posts SET score = score - 1 WHERE id = ?", (link_id,))
    db.commit()
    return redirect(url_for("homepage"))


@app.post('/hide/<int:link_id>')
def hide(link_id: int):
    db = get_db()
    db.execute("UPDATE posts SET hidden = 1 WHERE id = ?", (link_id,))
    db.commit()
    return redirect(url_for("homepage"))


@app.post('/unhide/<int:link_id>')
def unhide(link_id: int):
    db = get_db()
    db.execute("UPDATE posts SET hidden = 0 WHERE id = ?", (link_id,))
    db.commit()
    return redirect(url_for("homepage"))

@app.post('/submit')
def submit():
    """Handle new-post submissions from the homepage form.

    Minimal validation: non-empty title and URL starting with 'http'.
    On success: append to `dog_links` with `score=1` and redirect to `/`.
    On validation error: re-render the homepage with a friendly message and
    the submitted values so the user can fix them.
    """
    title = (request.form.get("title") or "").strip()
    url = (request.form.get("url") or "").strip()

    if not title or not url.lower().startswith("http"):
        db = get_db()
        visible = db.execute("SELECT id, title, url, score, hidden, created_at FROM posts WHERE hidden = 0 ORDER BY score DESC").fetchall()
        hidden = db.execute("SELECT id, title, url, score, hidden, created_at FROM posts WHERE hidden = 1 ORDER BY score DESC").fetchall()
        visible_links = [dict(r) for r in visible]
        hidden_links = [dict(r) for r in hidden]
        error = "Please provide a title and a valid URL starting with http."
        return render_template("index.html", links=visible_links, hidden_posts=hidden_links, error=error, form_title=title, form_url=url)

    db = get_db()
    db.execute("INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, 1, 0)", (title, url))
    db.commit()
    return redirect(url_for("homepage"))
