from flask import Flask, redirect, request, session, url_for, render_template_string
import requests
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace these with your GitHub OAuth credentials
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', 'YOUR_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>GitHub OAuth Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f0f0f0; }
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .btn { display: inline-block; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; }
        .github-btn { background: #24292e; color: white; }
        .github-btn:hover { background: #1b1f23; }
        .logout-btn { background: #dc3545; color: white; }
        .user-info { display: flex; align-items: center; gap: 20px; margin: 20px 0; }
        .avatar { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #eee; }
        .details p { margin: 5px 0; color: #666; }
        .details strong { color: #333; }
        pre { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
    </style>
</head>
<body>
    <div class="card">
    {% if user %}
        <h1>🎉 Login Successful!</h1>
        <div class="user-info">
            <img src="{{ user.avatar_url }}" class="avatar">
            <div class="details">
                <h2 style="margin:0;">{{ user.name or user.login }}</h2>
                <p><strong>Username:</strong> {{ user.login }}</p>
                <p><strong>Email:</strong> {{ user.email or 'Private' }}</p>
                <p><strong>Location:</strong> {{ user.location or 'Not set' }}</p>
                <p><strong>Public Repos:</strong> {{ user.public_repos }}</p>
                <p><strong>Followers:</strong> {{ user.followers }}</p>
            </div>
        </div>
        <h3>Full API Response:</h3>
        <pre>{{ user_json }}</pre>
        <form action="/logout" method="post" style="margin-top:20px;">
            <button type="submit" class="btn logout-btn">Logout</button>
        </form>
    {% else %}
        <h1>🔐 GitHub OAuth 2.0 Demo</h1>
        <p>Click below to authenticate with your GitHub account:</p>
        <br>
        <a href="/login" class="btn github-btn">⚡ Login with GitHub</a>
    {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    user = session.get('user')
    user_json = json.dumps(user, indent=2) if user else None
    return render_template_string(HTML, user=user, user_json=user_json)

@app.route('/login')
def login():
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={url_for('authorize', _external=True)}"
        f"&scope=read:user"
    )
    return redirect(auth_url)

@app.route('/authorize')
def authorize():
    code = request.args.get('code')
    if not code:
        return "Error: No code", 400

    # Exchange code for token
    resp = requests.post(
        'https://github.com/login/oauth/access_token',
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
        },
        headers={'Accept': 'application/json'}
    )
    token = resp.json().get('access_token')
    
    if not token:
        return f"Error: {resp.json()}", 400

    # Get user info
    user = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'Bearer {token}'}
    ).json()

    session['user'] = user
    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print(f"Server running at http://localhost:5003")
    app.run(host='0.0.0.0', port=5003, debug=True)