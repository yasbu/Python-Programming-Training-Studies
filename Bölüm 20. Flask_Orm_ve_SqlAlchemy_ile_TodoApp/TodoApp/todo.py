from flask import Flask, render_template, redirect,url_for,request
from flask_sqlalchemy import SQLAlchemy


# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////Users/yasin/Desktop/Yeni klasör/TodoApp/todo.db"
# initialize the app with the extension
db.init_app(app)

@app.route('/')
def index():
    todos = Todo.query.all()
    return render_template('index.html', todos=todos)

@app.route('/complete/<string:id>')
def completeTodo(id):
    todo =Todo.query.filter_by(id=id).first()
    """if todo.complete == True:
        todo.complete = False
    else:
        todo.complete = True"""
    todo.complete = not todo.complete

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<string:id>')
def deleteTodo(id):
    todo =Todo.query.filter_by(id=id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add',methods=['POST'])
def addTodo():
    title = request.form.get('title')
    newTodo = Todo(title=title,complete=False)
    db.session.add(newTodo)
    db.session.commit()

    return redirect(url_for('index'))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    complete = db.Column(db.Boolean)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)