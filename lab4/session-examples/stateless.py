from flask import Flask, request, jsonify, render_template_string
import jwt
import datetime
import os

app = Flask(__name__)
# This secret key is used to SIGN the JWTs. 
# Anyone with this key can forge tokens.
SECRET_KEY = os.urandom(24) 

USERS = {
    'admin': 'secret',
    'alice': 'password123'
}

# Simple Single Page App (SPA) simulation to handle JWT in headers
HTML_CLIENT = '''
<!DOCTYPE html>
<html>
<head>
    <title>JWT Auth Demo</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
        .box { border: 1px solid #ccc; padding: 20px; border-radius: 8px; background: #f9f9f9; }
        input { display: block; margin: 10px 0; padding: 5px; width: 100%; }
        button { background: #28a745; color: white; border: none; padding: 10px 20px; cursor: pointer; }
        .logout { background: #dc3545; }
        #status { margin-bottom: 10px; font-weight: bold; }
        pre { background: #333; color: #fff; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Stateless JWT Demo</h1>
    <div id="status">Not Logged In</div>

    <!-- LOGIN FORM -->
    <div id="login-box" class="box">
        <h2>Login</h2>
        <input type="text" id="username" placeholder="Username (try: admin)">
        <input type="password" id="password" placeholder="Password (try: secret)">
        <button onclick="login()">Get JWT Token</button>
    </div>

    <!-- LOGGED IN VIEW -->
    <div id="content-box" class="box" style="display:none;">
        <h2>Logged In!</h2>
        <p>You are authenticated via a <strong>Bearer Token</strong> (JWT).</p>
        
        <h3>Your Token (Stored in LocalStorage):</h3>
        <pre id="token-display" style="font-size: 10px; word-break: break-all;"></pre>
        
        <h3>Protected Data from Server:</h3>
        <pre id="data-display">Loading...</pre>

        <button class="logout" onclick="logout()">Logout</button>
    </div>

    <h3>How it works:</h3>
    <ul>
        <li><strong>Login:</strong> Send creds map via JSON -> Server validates -> Generates signed JWT -> Returns string.</li>
        <li><strong>Storage:</strong> JavaScript saves token to <code>localStorage</code> (Client-side).</li>
        <li><strong>Request:</strong> JS attaches <code>Authorization: Bearer &lt;token&gt;</code> header to requests.</li>
        <li><strong>State:</strong> Stateless! Server just checks signature. No session lookup.</li>
    </ul>

    <script>
        const API_URL = 'http://localhost:5003';

        // Check if we already have a token
        if (localStorage.getItem('token')) {
            showLoggedIn(localStorage.getItem('token'));
        }

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // IMPORTANT: We store the token on the client
                localStorage.setItem('token', data.token);
                showLoggedIn(data.token);
            } else {
                alert('Login failed: ' + data.message);
            }
        }

        async function showLoggedIn(token) {
            document.getElementById('login-box').style.display = 'none';
            document.getElementById('content-box').style.display = 'block';
            document.getElementById('status').innerText = 'State: Authenticated';
            document.getElementById('token-display').innerText = token;

            // Fetch protected data using the token
            fetchProtectedData(token);
        }

        async function fetchProtectedData(token) {
            const response = await fetch(`${API_URL}/protected`, {
                method: 'GET',
                // IMPORTANT: We must manually send the token
                headers: { 
                    'Authorization': `Bearer ${token}` 
                }
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('data-display').innerText = JSON.stringify(data, null, 2);
            } else {
                // Token might be expired
                document.getElementById('data-display').innerText = "Error: " + response.statusText;
                if (response.status === 401) logout(); 
            }
        }

        function logout() {
            // LOGOUT LOGIC:
            // Just delete the token from the client. The server doesn't even know!
            localStorage.removeItem('token');
            location.reload(); 
        }
    </script>
</body>
</html>
'''

# Serves the static HTML Client
@app.route('/')
def home():
    return render_template_string(HTML_CLIENT)

# API Endpoint: Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in USERS and USERS[username] == password:
        # JWT GENERATION LOGIC:
        # Create a payload with user data and expiration
        payload = {
            'sub': username,
            'role': 'admin' if username == 'admin' else 'user',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30) # Expires in 30 mins
        }
        # Sign it
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

# API Endpoint: Protected Resource
@app.route('/protected', methods=['GET'])
def protected():
    # JWT VERIFICATION LOGIC:
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({'message': 'Missing Token'}), 401
    
    token = auth_header.split(" ")[1]
    
    try:
        # Verify signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({
            'message': 'Welcome to the protected data!',
            'user': payload['sub'],
            'role': payload['role'],
            'secure_info': 'Only people with a valid token see this.'
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token Expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401

if __name__ == '__main__':
    print("Running JWT Demo on http://localhost:5003")
    app.run(port=5003, debug=True)
