import os

from flask import Flask, render_template, g, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db

app = Flask(__name__)
app.config['SECRET_KEY']  = os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    if 'user' in session:
        user = session["user"]
        return render_template('home.html', user=user)
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # return f'Name: {request.form["name"]}, Password: {request.form["password"]}'
        db = get_db()
        hashed_password = generate_password_hash(request.form["password"], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)', [request.form["name"], hashed_password, 0, 0])
        db.commit()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        name = request.form["name"]
        password = request.form["password"]
        user_cursor = db.execute('select id, name, password from users where name = ?', [name])
        user_result = user_cursor.fetchone()

        if check_password_hash(user_result["password"], password):
            session["user"] = user_result["name"]
            return "Password correct"
        else:
            return "Wrong password"


    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/question')
def question():
    return render_template('question.html')

@app.route('/answer')
def answer():
    return render_template('answer.html')

@app.route('/ask')
def ask():
    return render_template('ask.html')

@app.route('/unanswered')
def unanswered():
    return render_template('unanswered.html')

@app.route('/users')
def users():
    return render_template('users.html')

if __name__ == '__main__':
    app.run(debug=True)