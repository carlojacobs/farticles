# Dependencies
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import datetime
from bson.objectid import ObjectId

# Flask
app = Flask(__name__)

# pymongo
client = MongoClient('mongodb://carlo:Dittoenbram1234@carlo-shard-00-00-nwaxe.mongodb.net:27017,carlo-shard-00-01-nwaxe.mongodb.net:27017,carlo-shard-00-02-nwaxe.mongodb.net:27017/test?ssl=true&replicaSet=carlo-shard-0&authSource=admin')
db = client.farticles

# Users collection
users = db.users
# Articles collection
articles = db.articles

# Routes

# Home
@app.route('/')
def index():
	return render_template('home.html')

# About
@app.route('/about')
def about():
	return render_template('about.html')

# Register form class
class RegisterForm(Form):

	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords do not match')
	])
	confirm = PasswordField('Confirm password')

# User register
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)

	# Check if post or get request
	if request.method == 'POST' and form.validate():

		# form data
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		newUser = {
			"name": name,
			"email": email,
			"username": username,
			"password": password
		}

		users.insert_one(newUser)
		flash('Registered successfully', 'success')
		return redirect(url_for('login'))

	return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():

	if request.method == 'POST':
		# form data
		username = request.form['username']
		password_candidate = request.form['password']

		user = users.find_one({"username": username})

		if user != None:
			password = user['password']

			# Compare passwords
			if sha256_crypt.verify(password_candidate, password):
				# Passed
				session['logged_in'] = True
				session['username'] = username
				session['name'] = user['name']

				flash('Logged in successfully!', 'success')
				return redirect(url_for('dashboard'))

			else:
				error = 'Oops! Wrong password...'
				return render_template('login.html', error=error)

		else:
			error = "Oops! A user with this username doesn't exist"
			return render_template('login.html', error=error)


	return render_template('login.html')

# Check if user is logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, please log in.', 'danger')
			return redirect(url_for('login'))

	return wrap

# Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out.', 'success')
	return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

	my_articles = articles.find({"author": session['username']})

	if my_articles != None:
		return render_template('dashboard.html', articles=my_articles)
	else:
		message = 'No articles found'
		return render_template('dashboard.html', message=message)


# Article form class
class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min=5, max=200)])
	body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)

	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		newArticle = {
			"title": title,
			"body": body,
			"author": session['username'],
			"date": datetime.datetime.utcnow()
		}

		articles.insert_one(newArticle)
		flash('Posted article successfully.', 'success')
		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)

# Fetch one article
@app.route('/article/<string:id>')
@is_logged_in
def article(id):
	
	article_found = articles.find_one({"_id": ObjectId(id)})
	return render_template('article.html', article=article_found)

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):

	article_found = articles.find_one({"_id": ObjectId(id)})

	form = ArticleForm(request.form)

	form.title.data = article_found['title']
	form.body.data = article_found['body']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']
		app.logger.info(title, body)
		updatedArticle = {
			"_id": ObjectId(id),
			"title": title,
			"body": body,
			"author": session['username'],
			"date": datetime.datetime.utcnow()
		}

		articles.save(updatedArticle)
		flash('Edited article successfully.', 'success')
		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	
	articles.delete_one({"_id": ObjectId(id)})
	flash('Farticle deleted.', 'success')
	return redirect(url_for('dashboard'))

if __name__ == '__main__':
	app.secret_key = 'mysecretkey123'
	app.run(debug=True)