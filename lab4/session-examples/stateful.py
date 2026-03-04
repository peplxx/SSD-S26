from flask import Flask, request, redirect, url_for, session, render_template_string
import os

app = Flask(__name__)
# The secret key is used to cryptographically sign the session cookie
app.secret_key = os.urandom(24)

# Mock User Database
USERS = {
    'admin': 'secret',
    'alice': 'password123'
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Session Auth Demo</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
        .box { border: 1px solid #ccc; padding: 20px; border-radius: 8px; background: #f9f9f9; }
        input { display: block; margin: 10px 0; padding: 5px; width: 100%; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; }
        .logout { background: #dc3545; }
        pre { background: #eee; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Server-Side Session Demo</h1>
    
    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}

    {% if user %}
        <div class="box">
            <h2>Welcome, {{ user }}!</h2>
            <p>You are authenticated via a <strong>Signed Session Cookie</strong>.</p>
            
            <h3>Your Session Data (Server-Side):</h3>
            <pre>{{ session_data }}</pre>

            <form action="{{ url_for('logout') }}" method="post">
                <button type="submit" class="logout">Logout</button>
            </form>
        </div>
    {% else %}
        <div class="box">
            <h2>Login</h2>
            <form action="{{ url_for('login') }}" method="post">
                <label>Username (try: admin)</label>
                <input type="text" name="username" required>
                <label>Password (try: secret)</label>
                <input type="password" name="password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    {% endif %}
    
    <h3>How it works:</h3>
    <ul>
        <li><strong>Login:</strong> Server validates creds -> Creates dictionary <code>session['user'] = username</code> -> Signs it -> Sends standard cookie.</li>
        <li><strong>Request:</strong> Browser sends cookie -> Flask verifies signature -> Decodes data into <code>session</code> object.</li>
        <li><strong>State:</strong> Stored on the server (or in the signed cookie payload itself).</li>
    </ul>
</body>
</html>
'''

@app.route('/')
def home():
    if 'user' in session:
        # We can see the actual session object here
        return render_template_string(HTML_TEMPLATE, user=session['user'], session_data=dict(session))
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username in USERS and USERS[username] == password:
        # SESSION LOGIC:
        # We just add keys to the global 'session' dict.
        # Flask handles serializing this and signing it into a cookie.
        session['user'] = username
        session['role'] = 'admin' if username == 'admin' else 'user'
        return redirect(url_for('home'))
    
    return render_template_string(HTML_TEMPLATE, error="Invalid credentials")

@app.route('/logout', methods=['POST'])
def logout():
    # SESSION LOGIC:
    # Remove the keys. The next response will update the cookie to be empty/invalid.
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    print("Running Session Demo on http://localhost:5002")
    app.run(port=5002, debug=True)
