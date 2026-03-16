from flask import Flask, redirect, request, session, url_for, render_template_string
import requests
import jwt
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# KeyCloak Configuration
KEYCLOAK_URL = "http://localhost:9000"
REALM = "myrealm"
CLIENT_ID = "myapp"
CLIENT_SECRET = os.environ.get('KEYCLOAK_SECRET', 'YOUR_CLIENT_SECRET')

# Endpoints
AUTH_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
LOGOUT_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout"

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>KeyCloak SSO Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 90vh; }
        .card { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .btn { display: inline-block; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; font-size: 16px; }
        .login-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .logout-btn { background: #ef4444; color: white; }
        .user-card { background: #f8f9fa; border-radius: 12px; padding: 25px; margin: 20px 0; }
        .user-header { display: flex; align-items: center; gap: 20px; }
        .avatar { width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 28px; font-weight: bold; }
        .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px; }
        .info-item { background: white; padding: 15px; border-radius: 8px; }
        .info-label { font-size: 12px; color: #888; text-transform: uppercase; }
        .info-value { font-size: 16px; color: #333; font-weight: 500; margin-top: 5px; }
        .role-badge { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        pre { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 11px; }
        .section-title { font-size: 16px; font-weight: 600; color: #333; margin: 25px 0 10px 0; border-bottom: 2px solid #eee; padding-bottom: 8px; }
    </style>
</head>
<body>
    <div class="card">
    {% if user %}
        <h1>🎉 Welcome to the App!</h1>
        <p class="subtitle">Authenticated via KeyCloak SSO</p>
        
        <div class="user-card">
            <div class="user-header">
                <div class="avatar">{{ (user.preferred_username or 'U')[0].upper() }}</div>
                <div>
                    <h2 style="margin:0;">{{ user.name or user.preferred_username }}</h2>
                    <p style="margin:5px 0; color:#666;">{{ user.email or 'No email' }}</p>
                </div>
            </div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Username</div>
                    <div class="info-value">{{ user.preferred_username }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email Verified</div>
                    <div class="info-value">{{ '✅ Yes' if user.email_verified else '❌ No' }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Roles</div>
                    <div class="info-value">
                        {% for role in roles %}
                            <span class="role-badge">{{ role }}</span>
                        {% else %}
                            None
                        {% endfor %}
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">Session</div>
                    <div class="info-value">Active ✅</div>
                </div>
            </div>
        </div>

        <div class="section-title">🔑 Access Token (decoded)</div>
        <pre>{{ token_data }}</pre>
        
        <form action="/logout" method="post" style="margin-top:25px;">
            <button type="submit" class="btn logout-btn">🚪 Logout</button>
        </form>
    {% else %}
        <h1>🔐 KeyCloak SSO Demo</h1>
        <p class="subtitle">Single Sign-On with OpenID Connect</p>
        <p style="color:#666; margin-bottom:30px;">Click below to login using your KeyCloak account (user1 / password123)</p>
        <a href="/login" class="btn login-btn">🔑 Login with KeyCloak</a>
        
        <div class="section-title" style="margin-top:40px;">How SSO Works</div>
        <ol style="color:#666; line-height:2;">
            <li>Click "Login with KeyCloak"</li>
            <li>Redirect to KeyCloak login page</li>
            <li>Enter credentials (user1 / password123)</li>
            <li>KeyCloak issues tokens (ID + Access)</li>
            <li>Redirect back with user profile</li>
        </ol>
    {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    user = session.get('user')
    roles = session.get('roles', [])
    token_data = session.get('token_data', '')
    return render_template_string(HTML, user=user, roles=roles, token_data=token_data)

@app.route('/login')
def login():
    auth_url = (
        f"{AUTH_URL}"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid profile email"
        f"&redirect_uri={url_for('callback', _external=True)}"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code", 400

    # Exchange code for tokens
    resp = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': url_for('callback', _external=True)
    })

    if resp.status_code != 200:
        return f"Token error: {resp.text}", 400

    tokens = resp.json()
    access_token = tokens['access_token']

    # Decode token (without verification for display)
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    
    # Get user info
    user_resp = requests.get(USERINFO_URL, headers={
        'Authorization': f'Bearer {access_token}'
    })
    user = user_resp.json()

    # Extract roles
    roles = []
    if 'resource_access' in decoded and CLIENT_ID in decoded['resource_access']:
        roles = decoded['resource_access'][CLIENT_ID].get('roles', [])

    # Store in session
    session['user'] = user
    session['roles'] = roles
    session['token_data'] = json.dumps(decoded, indent=2)
    session['id_token'] = tokens.get('id_token')

    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    id_token = session.get('id_token')
    session.clear()
    
    if id_token:
        logout_url = f"{LOGOUT_URL}?id_token_hint={id_token}&post_logout_redirect_uri={url_for('home', _external=True)}"
        return redirect(logout_url)
    
    return redirect('/')

if __name__ == '__main__':
    print(f"SSO App running at http://localhost:5004")
    print(f"KeyCloak: {KEYCLOAK_URL}")
    app.run(host='0.0.0.0', port=5004, debug=True)
