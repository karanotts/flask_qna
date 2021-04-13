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

def get_current_user():
    user_result = None
    if 'user' in session:
        user = session["user"]
    
        db = get_db()
        user_cursor = db.execute('select id, name, password, expert, admin from users where name = ?', [user])
        user_result = user_cursor.fetchone()
    
    return user_result


@app.route('/')
def index():
    user = get_current_user()
    return render_template('home.html', user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if request.method == 'POST':
        # return f'Name: {request.form["name"]}, Password: {request.form["password"]}'
        db = get_db()
        hashed_password = generate_password_hash(request.form["password"], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)', [request.form["name"], hashed_password, 0, 0])
        db.commit()
        return redirect(url_for('index'))

    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        name = request.form["name"]
        password = request.form["password"]
        user_cursor = db.execute('select id, name, password from users where name = ?', [name])
        user_result = user_cursor.fetchone()

        if user_result:
            if check_password_hash(user_result["password"], password):
                session["user"] = user_result["name"]
                return redirect(url_for('index'))
            else:
                return "Wrong password"
        else:
            return "Wrong username"

    return render_template('login.html', user=user)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/question')
def question():
    user = get_current_user()
    return render_template('question.html', user=user)


@app.route('/answer')
def answer():
    user = get_current_user()
    return render_template('answer.html', user=user)

@app.route('/ask')
def ask():
    user = get_current_user()
    return render_template('ask.html', user=user)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    return render_template('unanswered.html', user=user)


@app.route('/users')
def users():
    user = get_current_user()
    db = get_db()
    users_cursor = db.execute('select id, name, expert, admin from users')
    users_result = users_cursor.fetchall()
    return render_template('users.html', user=user, users=users_result)

@app.route('/edit/<user_id>')
def edit(user_id):
    db = get_db()
    db.execute('update users set expert = 1 where id = ?', [user_id])
    user_cursor = db.execute('select name from users where id = ?', [user_id]
    user = user_cursor.fetchone()
    db.commit()

    return f"Promoted user {user['name']} to expert"


if __name__ == '__main__':
    app.run(debug=True)