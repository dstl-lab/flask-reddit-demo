# from flask import Flask, render_template

# app = Flask(__name__)

# dog_links = [
#     {
#         "title": "30 Fun and Fascinating Dog Facts",
#         "url": "https://www.akc.org/expert-advice/lifestyle/dog-facts/",
#         "score": 10,
#     },
#     {
#         "title": "Why Do Dogs Tilt Their Heads?",
#         "url": "https://www.sciencefocus.com/nature/why-do-dogs-tilt-their-head-when-you-speak-to-them",
#         "score": 5,
#     },
#     {
#         "title": "r/dogs — top posts",
#         "url": "https://www.reddit.com/r/dogs/",
#         "score": 3,
#     },
#     {
#         "title": "Basic Dog Training Guide",
#         "url": "https://www.animalhumanesociety.org/resource/how-get-most-out-training-your-dog",
#         "score": 2,
#     },
#     {
#         "title": "The Dogist (photo stories)",
#         "url": "https://thedogist.com/",
#         "score": 1,
#     },
# ]


# @app.get("/")
# def homepage():
#     return render_template("index.html", links=dog_links)


import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, g

# ---------- Config ----------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")
DATABASE = os.path.join(app.root_path, "posts.db")


# ---------- DB helpers ----------
def get_db():
    """Return a sqlite3.Connection for the current request context (cached on g)."""
    db = getattr(g, "_database", None)
    if db is None:
        # ensure the DB file exists (init will create tables/seed later)
        db = g._database = sqlite3.connect(
            DATABASE, detect_types=sqlite3.PARSE_DECLTYPES
        )
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            hidden INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    db.commit()


def seed_if_empty():
    """Seed starter posts only when the posts table is empty."""
    db = get_db()
    cur = db.execute("SELECT COUNT(*) AS c FROM posts")
    count = cur.fetchone()["c"]
    if count == 0:
        starter = [
            (
                "30 Fun and Fascinating Dog Facts",
                "https://www.akc.org/expert-advice/lifestyle/dog-facts/",
                10,
                0,
            ),
            (
                "Why Do Dogs Tilt Their Heads?",
                "https://www.sciencefocus.com/nature/why-do-dogs-tilt-their-head-when-you-speak-to-them",
                5,
                0,
            ),
            ("r/dogs — top posts", "https://www.reddit.com/r/dogs/", 3, 0),
            (
                "Basic Dog Training Guide",
                "https://www.animalhumanesociety.org/resource/how-get-most-out-training-your-dog",
                2,
                0,
            ),
            ("The Dogist (photo stories)", "https://thedogist.com/", 1, 0),
        ]
        db.executemany(
            "INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, ?, ?)",
            starter,
        )
        db.commit()


# ---------- Routes ----------
@app.get("/")
def homepage():
    """
    Render index.html with two lists:
    visible: non-hidden posts, sorted by score desc
    hidden: hidden posts, sorted by score desc
    """
    db = get_db()
    visible = db.execute(
        "SELECT * FROM posts WHERE hidden = 0 ORDER BY score DESC, created_at DESC"
    ).fetchall()
    hidden = db.execute(
        "SELECT * FROM posts WHERE hidden = 1 ORDER BY score DESC, created_at DESC"
    ).fetchall()
    return render_template("index.html", visible=visible, hidden=hidden)


@app.post("/vote/<int:post_id>")
def vote(post_id):
    """
    Handle form POSTs with hidden field 'direction' = 'up' or 'down'.
    After updating, redirect back to homepage so the page refreshes.
    """
    direction = request.form.get("direction")
    db = get_db()
    # Check post exists
    row = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if row is None:
        flash("Post not found.", "error")
        return redirect(url_for("homepage"))

    if direction == "up":
        db.execute("UPDATE posts SET score = score + 1 WHERE id = ?", (post_id,))
    elif direction == "down":
        db.execute("UPDATE posts SET score = score - 1 WHERE id = ?", (post_id,))
    else:
        flash("Invalid vote direction.", "error")
        return redirect(url_for("homepage"))

    db.commit()
    return redirect(url_for("homepage"))


@app.post("/submit")
def submit():
    """
    Adds new post
    """
    title = (request.form.get("title") or "").strip()
    url = (request.form.get("url") or "").strip()

    if not title:
        flash("Title cannot be empty.", "error")
        return redirect(url_for("homepage"))

    if not (url.startswith("http://") or url.startswith("https://")):
        flash("URL must start with http:// or https://", "error")
        return redirect(url_for("homepage"))

    db = get_db()
    db.execute(
        "INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, ?, 0)",
        (title, url, 1),
    )
    db.commit()
    flash("Post submitted!", "success")
    return redirect(url_for("homepage"))


@app.post("/hide/<int:post_id>")
def hide(post_id):
    """
    Mark a post as hidden (hidden = 1)
    """
    db = get_db()
    row = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if row is None:
        flash("Post not found.", "error")
    else:
        db.execute("UPDATE posts SET hidden = 1 WHERE id = ?", (post_id,))
        db.commit()
    return redirect(url_for("homepage"))


# ---------- Run ----------
if __name__ == "__main__":
    # ensure DB folder exists (app.root_path is used), then run
    with app.app_context():
        init_db()
        seed_if_empty()
    app.run(debug=True)
