from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    firstname = db.Column(db.String)

    def __init__(self, username, firstname):
        self.username = username
        self.firstname = firstname

    def __repr__(self):
        return '<User %r>' % self.username

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String, nullable=True)
    question = db.Column(db.String, nullable=False)
    answer = db.Column(db.String, nullable=False)

    image = db.Column(db.String)
    music = db.Column(db.String)

    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    quiz = db.relationship('Quiz',
        backref=db.backref('quizes', lazy='dynamic'))

    order = db.Column(db.Integer)

    def __init__(self, category, question, answer, image=None, music=None, quiz_id=None, number=None):
        self.category = category
        self.question = question
        self.answer = answer

        self.image = image
        self.music = music

        self.quiz_id = quiz_id
        self.order = order

    def __repr__(self):
        return '<Question %r>' % self.question

class Quiz(db.Model):
    #__tablename__ = 'quizes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, unique=True, nullable=False)
    description = db.Column(db.String, nullable=True)
    enabled = db.Column(db.Boolean, nullable=False)

    def __init__(self, name, date, description, enabled=False):
        self.name = name
        self.date = date
        self.description = description
        self.enabled = enabled

    def __repr__(self):
        return '<Quiz %r>' % self.name

class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User',
        backref=db.backref('users', lazy='dynamic'))

    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    quiz = db.relationship('Quiz',
        backref=db.backref('quiz', lazy='dynamic'))

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    question = db.relationship('Question',
        backref=db.backref('questions', lazy='dynamic'))

    answer = db.Column(db.String, nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime)

    def __init__(self, user_id, quiz_id, question_id, answer, correct, timestamp=None):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.question_id = question_id
        self.answer = answer
        self.correct = correct
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.timestamp = timestamp

    def __repr__(self):
        return '<Answer %r>' % self.id

#@app.route('/')
#def index():
#   return render_template('index.html')

#@app.route('/users')
#def users():
#   return render_template('users.html', users = User.query.all())

#@app.route('/questions')
#def questions():
#   return render_template('questions.html', questions = Question.query.all())

#@app.route('/quiz')
#def quizes():
#   return render_template('quizes.html', quizes = Quiz.query.all())

#@app.route('/quiz/<date>')
#def quiz_date(date):
#    quiz = Quiz.query.filter_by(date=date).first_or_404()
#    questions = Question.query.filter_by(quiz_id=quiz.id).all()
#    return render_template('quiz.html', quiz=quiz, questions=questions)

@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    quizes = Quiz.query.filter_by(enabled=True).all()
    return render_template('user.html', user=user, quizes=quizes)

@app.route('/user/<username>/quiz/<date>')
def user_quiz(username, date):
    user = User.query.filter_by(username=username).first_or_404()
    quiz = Quiz.query.filter_by(enabled=True, date=date).first_or_404()
    questions = Question.query.filter_by(quiz_id=quiz.id).order_by(Question.order).all()
    answers = Answer.query.filter_by(quiz_id=quiz.id, user_id=user.id).all()

    join = db.session.query(Question, Answer).join(Answer).filter_by(quiz_id=quiz.id, user_id=user.id).order_by(Question.order).all()

    return render_template('user_quiz.html', user=user, quiz=quiz, questions=questions, answers=answers, join=join)

@app.route('/user/<username>/quiz/<date>/delete', methods = ['POST'])
def delete_user_quiz(username, date):
    user_id = int(request.form['user_id'])
    quiz_id = int(request.form['quiz_id'])

    Answer.query.filter(Answer.user_id == user_id, Answer.quiz_id == quiz_id).delete()
    db.session.commit()

    return redirect(request.form['url'])

@app.route('/user/<username>/quiz/<date>/question/done')
def user_quiz_done(username, date):
    user = User.query.filter_by(username=username).first_or_404()
    quiz = Quiz.query.filter_by(date=date).first_or_404()

    return render_template('user_quiz_done.html', user=user, quiz=quiz)

@app.route('/user/<username>/quiz/<date>/question/<question>')
def user_quiz_question(username, date, question):
    user = User.query.filter_by(username=username).first_or_404()
    quiz = Quiz.query.filter_by(date=date).first_or_404()

    questions = Question.query.filter_by(quiz_id=quiz.id).count()
    q = Question.query.filter_by(quiz_id=quiz.id, order=question).first_or_404()

    return render_template('user_quiz_question.html', user=user, quiz=quiz, questions=questions, question=q)

@app.route('/answer', methods = ['POST'])#['GET', 'POST'])
def answer():
    print(request.form)

    answer = Answer(
        int(request.form['user_id']),
        int(request.form['quiz_id']),
        int(request.form['question_id']),
        request.form['answer'],
        int(request.form['correct'])
    )

    exists = db.session.query(Answer).filter_by(user_id=answer.user_id, question_id=answer.question_id).scalar() is not None
    if exists:
        print("allerede svart")
        # flash?
    else:
        print("aldri svart")
        db.session.add(answer)
        db.session.commit()

    return redirect(request.form['url'])

if __name__ == '__main__':
   db.create_all()
   app.run(debug = True, host = '0.0.0.0', port = 8080)
