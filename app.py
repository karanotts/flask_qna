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
    db = get_db()

    questions_cursor = db.execute('''select questions.id, questions.question_text, 
                                            askers.name as asker_name, 
                                            experts.name as expert_name
                                        from questions 
                                    join users as askers on askers.id = questions.asked_by_id
                                    join users as experts on experts.id = questions.expert_id
                                    where questions.answer_text is not null''')
    questions_result = questions_cursor.fetchall()

    return render_template('home.html', user=user, questions=questions_result)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    
    if request.method == 'POST':
        # return f'Name: {request.form["name"]}, Password: {request.form["password"]}'
        db = get_db()
        user_exists_cursor = db.execute('select id from users where name = ?', [request.form["name"]])
        user_exists_result = user_exists_cursor.fetchone()
        if user_exists_result:
            # return "This username is already taken"
            return render_template('register.html', user=user, error="This username is already taken, please select a different name.")

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


@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()
    question_cursor = db.execute('''select questions.id, questions.question_text, questions.answer_text,
                                            askers.name as asker_name, 
                                            experts.name as expert_name
                                        from questions 
                                    join users as askers on askers.id = questions.asked_by_id
                                    join users as experts on experts.id = questions.expert_id
                                    where questions.id = ?''', question_id)
    question_result = question_cursor.fetchone()

    return render_template('question.html', user=user, question=question_result)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        db.execute('update questions set answer_text = ? where id = ?', [request.form["answer"], question_id])
        db.commit()
        # return f'Answer to {question_id} is {request.form["answer"]}'
        return redirect(url_for('unanswered'))

    question_cursor = db.execute('select id, question_text from questions where id = ?', question_id)
    question_result = question_cursor.fetchone()

    return render_template('answer.html', user=user, question=question_result)

@app.route('/ask', methods=['GET', 'POST'])
def ask():

    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?)', [request.form["question"], user["id"], request.form["expert"]])
        db.commit()
        return redirect(url_for('index'))

    expert_cursor = db.execute('select id, name from users where expert = 1')
    expert_results = expert_cursor.fetchall()

    return render_template('ask.html', user=user, experts=expert_results)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    db = get_db()
    questions_cursor = db.execute('''select questions.id, questions.question_text, users.name from questions 
                                    join users on users.id = questions.asked_by_id
                                    where answer_text is null and expert_id = ?''', [user["id"]])
    questions_result = questions_cursor.fetchall()

    return render_template('unanswered.html', user=user, questions=questions_result)


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
    db.commit()

    return f"Promoted user {user['name']} to expert"


if __name__ == '__main__':
    app.run(debug=True)