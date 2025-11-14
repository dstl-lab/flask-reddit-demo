import sqlite3
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

DB_PATH = Path(__file__).with_name("reddit.db")

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


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
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

    cur.execute("SELECT COUNT(*) FROM posts")
    (count,) = cur.fetchone()
    if count == 0:
        cur.executemany(
            "INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, ?, 0)",
            [(p["title"], p["url"], p["score"]) for p in SEED_POSTS],
        )

    conn.commit()
    conn.close()


init_db()


def split_links_from_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM posts ORDER BY score DESC, created_at DESC"
    )
    rows = cur.fetchall()
    conn.close()

    visible = [row for row in rows if not row["hidden"]]
    hidden = [row for row in rows if row["hidden"]]

    return visible, hidden

@app.get("/")
def homepage():
    visible_links, hidden_links = split_links_from_db()
    return render_template("index.html", links=visible_links, hidden_links=hidden_links)

@app.post("/vote")
def vote():
    post_id = int(request.form["post_id"])
    direction = request.form["direction"]

    delta = 1 if direction == "up" else -1

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE posts SET score = score + ? WHERE id = ?",
        (delta, post_id),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("homepage"))


@app.post("/submit")
def submit_post():
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()

    error = None
    if not title:
        error = "Title cannot be empty."
    elif not url.startswith("http"):
        error = "URL must start with http or https."

    if error:
        visible_links, hidden_links = split_links_from_db()
        return render_template(
            "index.html",
            links=visible_links,
            hidden_links=hidden_links,
            error=error,
            prev_title=title,
            prev_url=url,
        )

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, 1, 0)",
        (title, url),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("homepage"))


@app.post("/hide")
def hide_post():
    post_id = int(request.form["post_id"])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE posts SET hidden = 1 WHERE id = ?",
        (post_id,),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("homepage"))
