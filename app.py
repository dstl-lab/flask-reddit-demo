from flask import Flask, render_template, redirect, request, flash


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Track the next ID for new posts
next_id = 5

dog_links = [
    {
        "id": 0,
        "title": "30 Fun and Fascinating Dog Facts",
        "url": "https://www.akc.org/expert-advice/lifestyle/dog-facts/",
        "score": 10,
        "hidden": False,
    },
    {
        "id": 1,
        "title": "Why Do Dogs Tilt Their Heads?",
        "url": "https://www.sciencefocus.com/nature/why-do-dogs-tilt-their-head-when-you-speak-to-them",
        "score": 5,
        "hidden": False,
    },
    {
        "id": 2,
        "title": "r/dogs — top posts",
        "url": "https://www.reddit.com/r/dogs/",
        "score": 3,
        "hidden": False,
    },
    {
        "id": 3,
        "title": "Basic Dog Training Guide",
        "url": "https://www.animalhumanesociety.org/resource/how-get-most-out-training-your-dog",
        "score": 2,
        "hidden": False,
    },
    {
        "id": 4,
        "title": "The Dogist (photo stories)",
        "url": "https://thedogist.com/",
        "score": 1,
        "hidden": False,
    },
]


@app.get("/")
def homepage():
    visible_links = [link for link in dog_links if not link.get("hidden", False)]
    hidden_links = [link for link in dog_links if link.get("hidden", False)]
    
    # Sort both lists by score descending
    visible_links = sorted(visible_links, key=lambda x: x["score"], reverse=True)
    hidden_links = sorted(hidden_links, key=lambda x: x["score"], reverse=True)
    
    return render_template("index.html", visible_links=visible_links, hidden_links=hidden_links)


@app.post("/upvote/<int:link_id>")
def upvote(link_id):
    for link in dog_links:
        if link["id"] == link_id:
            link["score"] += 1
            break
    return redirect("/")


@app.post("/downvote/<int:link_id>")
def downvote(link_id):
    for link in dog_links:
        if link["id"] == link_id:
            link["score"] -= 1
            break
    return redirect("/")


@app.post("/hide/<int:link_id>")
def hide_post(link_id):
    for link in dog_links:
        if link["id"] == link_id:
            link["hidden"] = not link.get("hidden", False)
            break
    return redirect("/")


@app.post("/submit")
def submit_post():
    global next_id
    
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    
    # Validate: non-empty title and url starts with http
    if not title:
        flash('Error: Title is required!', 'error')
    elif not url.startswith("http"):
        flash('Error: URL must start with http:// or https://', 'error')
    else:
        dog_links.append({
            "id": next_id,
            "title": title,
            "url": url,
            "score": 1,
            "hidden": False,
        })
        next_id += 1
        flash('Post submitted successfully!', 'success')
    
    return redirect("/")