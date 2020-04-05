from flask import current_app,jsonify,Blueprint, render_template, request, redirect, url_for, make_response
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from application import mongo

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST','GET'])
def login():
	if 'errors' not in request.args:
		errors=[]
	else:
		errors = [request.args.get('errors')]
	if request.method=="POST":
		username = request.form.get('username')
		password = request.form.get('password')
		try:
			user = mongo.db.users.find_one_or_404({'username':username})
			if check_password_hash(user['password'],password):
				mongo.db.users.update_one({'username':user['username']},{'$set':{'last_logged':datetime.datetime.now()}})
				token = jwt.encode({'username': user['username'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, current_app.config['SECRET_KEY'])
				return jsonify({'token' : token.decode('UTF-8')})
			errors.append('Password is incorrect')
		except Exception as e:
			errors.append(f'User not found {e}')
	return jsonify({'errors':errors})


@auth.route('/register', methods=['POST','GET'])
def register():
	errors = []
	if request.method=="POST":
		username = request.form.get('username')
		try:
			mongo.db.users.find_one_or_404({'username':username})
			errors.append("User already exists")
		except Exception as e:
			password = request.form.get('password')
			confirm = request.form.get('confirm')
			if password==confirm:
				user = {'username':username,
				'password':generate_password_hash(password)}
				mongo.db.users.insert_one(user)
				return jsonify({'status':"User was created"})
			else:
				errors.append('Passwords do not match')
	return jsonify({'errors':errors})

@auth.route('/logout')
def logout():
	return jsonify({'action':"Logged out"})