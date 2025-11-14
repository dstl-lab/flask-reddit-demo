from flask import Flask, render_template, redirect, request, flash
import sqlite3

app = Flask(__name__)

# Secret key is required for Flask's flash messaging system (Feature B)
# In production, this should be a secure random value stored in environment variables
app.secret_key = "your-secret-key-here"

# Database configuration
DATABASE = "posts.db"


# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================

def get_db_connection():
    """
    Create and return a database connection.

    Sets row_factory to sqlite3.Row so we can access columns by name.
    This makes the returned rows behave like dictionaries.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the database schema.

    Creates the 'posts' table if it doesn't exist with columns:
    - id: Primary key, auto-incremented
    - title: Post title (required)
    - url: Post URL, used as unique identifier (required)
    - score: Vote score, starts at 1 for new posts (required)
    - hidden: Boolean flag (0=visible, 1=hidden), defaults to 0
    - created_at: Timestamp of creation, defaults to current time
    """
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            score INTEGER NOT NULL,
            hidden INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    """
    Seed the database with initial dog_links data.

    Only runs if the posts table is empty (first run).
    Inserts all posts from the dog_links list below.
    """
    conn = get_db_connection()

    # Check if database is empty
    count = conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()["count"]

    if count == 0:
        # Database is empty, seed it with initial data
        for link in dog_links:
            conn.execute(
                "INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, ?, ?)",
                (link["title"], link["url"], link["score"], 1 if link["hidden"] else 0)
            )
        conn.commit()
        print(f"Database seeded with {len(dog_links)} posts")

    conn.close()


# Initial data for seeding the database on first run
# NOTE: This list is only used once to populate the database if it's empty.
# After the first run, all data is stored in and loaded from the SQLite database.
# Each post has:
#   - title: Display name of the post
#   - url: Link URL (also used as unique identifier for finding posts)
#   - score: Upvote/downvote score (Feature A) - used for sorting posts
#   - hidden: Boolean flag (Feature C) - determines if post appears in main feed or hidden section
dog_links = [
    {
        "title": "30 Fun and Fascinating Dog Facts",
        "url": "https://www.akc.org/expert-advice/lifestyle/dog-facts/",
        "score": 10,
        "hidden": False,  # Feature C: All posts start visible
    },
    {
        "title": "Why Do Dogs Tilt Their Heads?",
        "url": "https://www.sciencefocus.com/nature/why-do-dogs-tilt-their-head-when-you-speak-to-them",
        "score": 5,
        "hidden": False,
    },
    {
        "title": "r/dogs — top posts",
        "url": "https://www.reddit.com/r/dogs/",
        "score": 3,
        "hidden": False,
    },
    {
        "title": "Basic Dog Training Guide",
        "url": "https://www.animalhumanesociety.org/resource/how-get-most-out-training-your-dog",
        "score": 2,
        "hidden": False,
    },
    {
        "title": "The Dogist (photo stories)",
        "url": "https://thedogist.com/",
        "score": 1,
        "hidden": False,
    },
]


# ============================================================================
# FEATURE A: UPVOTE/DOWNVOTE ROUTES
# ============================================================================

@app.post("/upvote")
def upvote():
    """
    Feature A: Increment the score of a post by 1

    Process:
    1. Receive the post's URL from the form submission
    2. Find the matching post in the database by URL
    3. Increment its score by 1 using SQL UPDATE
    4. Redirect to homepage, which will re-query and re-sort posts

    Note: We use URL as the unique identifier because post IDs are internal
    and URLs are guaranteed to be unique for each post.
    """
    url = request.form.get("url")

    # Update the score in the database
    conn = get_db_connection()
    conn.execute(
        "UPDATE posts SET score = score + 1 WHERE url = ?",
        (url,)
    )
    conn.commit()
    conn.close()

    # Redirect to homepage to show updated scores with proper sorting
    return redirect("/")


@app.post("/downvote")
def downvote():
    """
    Feature A: Decrement the score of a post by 1

    Process:
    1. Receive the post's URL from the form submission
    2. Find the matching post in the database by URL
    3. Decrement its score by 1 using SQL UPDATE
    4. Redirect to homepage, which will re-query and re-sort posts
    """
    url = request.form.get("url")

    # Update the score in the database
    conn = get_db_connection()
    conn.execute(
        "UPDATE posts SET score = score - 1 WHERE url = ?",
        (url,)
    )
    conn.commit()
    conn.close()

    # Redirect to homepage to show updated scores with proper sorting
    return redirect("/")


# ============================================================================
# FEATURE C: HIDE/UNHIDE POST ROUTE
# ============================================================================

@app.post("/toggle-hide")
def toggle_hide():
    """
    Feature C: Toggle the hidden status of a post

    Process:
    1. Receive the post's URL from the form submission
    2. Find the matching post in the database by URL
    3. Toggle its 'hidden' flag (0 → 1 or 1 → 0) using SQL
    4. Redirect to homepage, which will re-query and separate visible and hidden posts

    The same route handles both "Hide" and "Unhide" actions by toggling the flag.
    Note: In SQLite, we use INTEGER (0/1) instead of BOOLEAN (False/True).
    """
    url = request.form.get("url")

    # Toggle the hidden status in the database
    # We use CASE to flip 0 to 1 and 1 to 0
    conn = get_db_connection()
    conn.execute(
        "UPDATE posts SET hidden = CASE WHEN hidden = 0 THEN 1 ELSE 0 END WHERE url = ?",
        (url,)
    )
    conn.commit()
    conn.close()

    # Redirect to homepage to show updated post groupings
    return redirect("/")


# ============================================================================
# FEATURE B: SUBMIT NEW POST ROUTE
# ============================================================================

@app.post("/submit")
def submit():
    """
    Feature B: Create a new post from user submission

    Process:
    1. Receive title and URL from the form submission
    2. Validate inputs:
       - Title must be non-empty
       - URL must start with "http"
    3. If validation fails, show error message and redirect
    4. If validation passes, insert new post into database with score=1 and hidden=0
    5. Redirect to homepage to display the new post in proper sorted position
    """
    # Get form data and strip whitespace
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()

    # Validation: Title must be non-empty
    if not title:
        flash("Title cannot be empty")  # Show error message to user
        return redirect("/")

    # Validation: URL must start with "http" (http:// or https://)
    if not url.startswith("http"):
        flash("URL must start with http")  # Show error message to user
        return redirect("/")

    # All validations passed - insert the new post into the database
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO posts (title, url, score, hidden) VALUES (?, ?, ?, ?)",
        (title, url, 1, 0)  # score=1 (Feature B), hidden=0 (visible by default)
    )
    conn.commit()
    conn.close()

    # Redirect to homepage where the new post will appear sorted by score
    return redirect("/")


# ============================================================================
# HOMEPAGE ROUTE - Combines all features
# ============================================================================

@app.get("/")
def homepage():
    """
    Display the main page with sorted posts from the database

    Features combined:
    - Feature A: Posts are sorted by score (highest to lowest)
    - Feature C: Posts are separated into visible and hidden sections
    - Persistence: All data is loaded fresh from the SQLite database

    Process:
    1. Query visible posts (hidden=0) from database, sorted by score descending
    2. Query hidden posts (hidden=1) from database, sorted by score descending
    3. Pass both sorted lists to the template for rendering

    Implementation note: We sort hidden posts by score descending for consistency,
    so users can still see which hidden posts are most popular.
    """
    conn = get_db_connection()

    # Feature C + A: Query visible posts (hidden=0), sorted by score descending
    visible_links = conn.execute(
        "SELECT * FROM posts WHERE hidden = 0 ORDER BY score DESC"
    ).fetchall()

    # Feature C + A: Query hidden posts (hidden=1), sorted by score descending
    hidden_links = conn.execute(
        "SELECT * FROM posts WHERE hidden = 1 ORDER BY score DESC"
    ).fetchall()

    conn.close()

    # Pass both sorted lists to the template
    # 'links' contains visible posts for the main feed
    # 'hidden_links' contains hidden posts for the "Hidden posts" section
    return render_template("index.html", links=visible_links, hidden_links=hidden_links)


# ============================================================================
# DATABASE INITIALIZATION ON STARTUP
# ============================================================================

# Initialize the database schema and seed with initial data if empty
# This runs once when the Flask application starts
init_db()
seed_db()
