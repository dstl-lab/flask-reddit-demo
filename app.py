from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)


next_id = 6
dog_links = [
    {
        "id": 1,
        "title": "30 Fun and Fascinating Dog Facts",
        "url": "https://www.akc.org/expert-advice/lifestyle/dog-facts/",
        "score": 10,
        'hidden': False
    },
    {
        "id": 2,
        "title": "Why Do Dogs Tilt Their Heads?",
        "url": "https://www.sciencefocus.com/nature/why-do-dogs-tilt-their-head-when-you-speak-to-them",
        "score": 5,
        'hidden': False
    },
    {
        "id": 3,
        "title": "r/dogs — top posts",
        "url": "https://www.reddit.com/r/dogs/",
        "score": 3,
        'hidden': False
    },
    {
        "id": 4,
        "title": "Basic Dog Training Guide",
        "url": "https://www.animalhumanesociety.org/resource/how-get-most-out-training-your-dog",
        "score": 2,
        'hidden': False
    },
    {
        "id": 5,
        "title": "The Dogist (photo stories)",
        "url": "https://thedogist.com/",
        "score": 1,
        'hidden': False
    },
]


def find_post(post_id):
    for post in dog_links:
        if post['id'] == post_id:
            return post
    return None

@app.route('/vote/up/<int:post_id>')
def upvote(post_id):
    post = find_post(post_id)
    if post:
        post['score'] += 1
    return redirect(url_for('index'))

@app.route('/vote/down/<int:post_id>')
def downvote(post_id):
    post = find_post(post_id)
    if post:
        post['score'] -= 1
    return redirect(url_for('index'))

@app.route('/')
def index():
    visible_posts = []
    hidden_posts = []
    for post in dog_links:
        if post['hidden']:
            hidden_posts.append(post)
        else:
            visible_posts.append(post)
    
    sorted_visible = sorted(visible_posts, key=lambda p: p['score'], reverse=True)
    sorted_hidden = sorted(hidden_posts, key=lambda p: p['score'], reverse=True)
    return render_template('index.html', links=sorted_visible, hidden_posts=sorted_hidden)

@app.route('/hide/<int:post_id>')
def hide_post(post_id):
    post = find_post(post_id)
    if post:
        post['hidden'] = True
    return redirect(url_for('index'))

@app.route('/new', methods=['POST'])
def new_post():
    global next_id 
    
    title = request.form.get('title')
    url = request.form.get('url')

    if not title or not url or not (url.startswith('http://') or url.startswith('https://')):
        return "url is not in valid format"

    new_post = {
        'id': next_id,
        'title': title,
        'url': url,
        'score': 1,       
        'hidden': False   
    }
    dog_links.append(new_post)
    next_id += 1 

    
    return redirect(url_for('index'))