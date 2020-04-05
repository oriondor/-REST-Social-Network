from flask import Flask, Blueprint,jsonify,request,url_for,redirect
from functools import wraps
import datetime
import jwt
import json
from bson.objectid import ObjectId
from bson import json_util 
import sys
import requests


import config
from database import mongo

from auth import auth
from api import api_bpt

app = Flask(__name__)
app.config['MONGO_URI'] = config.mongo_uri
app.config['JSON_SORT_KEYS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY']='Th1s1ss3cr3t'
mongo.init_app(app)

def register_blueprints(app):
	app.register_blueprint(auth)
	app.register_blueprint(api_bpt)
register_blueprints(app)


def token_required(f):
	@wraps(f)
	def decorator(*args, **kwargs):
		#print('Actual headers are ', request.headers)
		token = None
		if 'x-access-tokens' in request.headers:
			token = request.headers['x-access-tokens']

		if not token:
			return jsonify({'message': 'a valid token is missing'})

		try:
			data = jwt.decode(token, app.config['SECRET_KEY'])
			current_user = mongo.db.users.find_one_or_404({'username':data['username']})
		except Exception as e:
			return jsonify({'message': f'token is invalid {e}'})

		return f(current_user, *args, **kwargs)
	return decorator

def token_optional(f):
	@wraps(f)
	def decorator(*args, **kwargs):
		#print('Actual headers are ', request.headers)
		token = None
		if 'x-access-tokens' in request.headers:
			token = request.headers['x-access-tokens']
		if token:
			try:
				data = jwt.decode(token, app.config['SECRET_KEY'])
				current_user = mongo.db.users.find_one_or_404({'username':data['username']})
			except Exception as e:
				return jsonify({'message': f'token is invalid {e}'})

			return f(current_user, *args, **kwargs)
		else:
			return f(None, *args, **kwargs)
	return decorator


@app.route('/')
@token_optional
def home(current_user):
	print(current_user)
	if current_user:
		print(current_user)
		req = requests.post(request.url_root+'log',data=json_util.dumps({'current_user':current_user,'activity':{'viewed_posts':datetime.datetime.now()}}))
		print(req.content)
	posts = [post for post in mongo.db.posts.find()]
	#print(posts)
	return json_util.dumps({'all_posts':posts})

@app.route('/new_post', methods=['POST','GET'])
@token_required
def new_post(current_user):
	data = json.loads(request.data)
	if request.method=="POST":
		if data['add_post']:
			text = data['new_text']
			date_now = datetime.datetime.now()
			likes={}
			post={
			'text':text,
			'author':current_user['username'],
			'likes':0,
			'likes_list':likes,
			'date':date_now,
			}
			#print('post is ', post)
			_id = mongo.db.posts.insert_one(post)
			#print(_id.inserted_id)
			req = requests.post(request.url_root+'log',data=json_util.dumps({'current_user':current_user,'activity':{'created_new_post':datetime.datetime.now()}}))
			#print(req.content)
			return json_util.dumps({'post_id':_id.inserted_id,'status':'Created'})
	return jsonify({'message':"Nothing happened"})

@app.route('/like', methods=["POST","GET"])
@token_required
def like(current_user):
	data = json.loads(request.data)
	print(data)
	if request.method=="POST" and 'post' in data and 'like' in data :
		user_id = current_user['_id']
		post_id = data['post']
		try:
			post = mongo.db.posts.find_one_or_404({'_id':ObjectId(post_id)})
		except Exception as e:
			return jsonify({'error':f"Post not found {e}"})
		likes_dict = post['likes_list']
		print(likes_dict)
		likes_accum = post['likes']
		if data['like']=='like':
			try:
				date_now = datetime.datetime.now()
				likes_dict.update({str(user_id):date_now})
				likes_accum += 1
				req = requests.post(request.url_root+'log',data=json_util.dumps({'current_user':current_user,'activity':{'liked_post':{post_id:datetime.datetime.now()}}}))
				print(req.content)
				mongo.db.posts.update_one({'_id':ObjectId(post_id)},{'$set':{'likes_list':likes_dict,'likes':likes_accum}})
				post = mongo.db.posts.find_one_or_404({'_id':ObjectId(post_id)})
				return json_util.dumps({'updated':post})
			except Exception as e:
				print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno),  e)
		elif data['like']=='dislike':			
			try:
				likes_dict.pop(str(user_id))
				likes_accum -= 1
				req = requests.post(request.url_root+'log',data=json_util.dumps({'current_user':current_user,'activity':{'disliked_post':{post_id:datetime.datetime.now()}}}))
				print(req.content)
				mongo.db.posts.update_one({'_id':ObjectId(post['_id'])},{'$set':{'likes_list':likes_dict,'likes':likes_accum}})
				post = mongo.db.posts.find_one_or_404({'_id':ObjectId(post_id)})
				return json_util.dumps({'updated':post})
			except Exception as e:
				print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), e)
	return jsonify({'message':"Nothing happened"})


@app.route('/delete', methods=["POST","GET"])
@token_required
def delete(current_user):
	if request.method=="POST":		
		data = json.loads(request.data)
		if 'delete' in data and data['delete']=="post_by_id":
			post_id = data['post_id']
			post = mongo.db.posts.find_one_or_404({'_id':ObjectId(post_id)})
			try:
				user = mongo.db.users.find_one_or_404({'username':post['author']})
			except:
				return jsonify({'error':"The author of this post is ghost or post not found"})
			if current_user['_id']!=user['_id']:
				return jsonify({"error":"You have no permissions to delete this post"})
			mongo.db.posts.delete_one({'_id':ObjectId(post_id)})
			req = requests.post(request.url_root+'log',data=json_util.dumps({'current_user':current_user,'activity':{'deleted_post':{post_id:datetime.datetime.now()}}}))
			print(req.content)
			return json_util.dumps({'message':f'Post {post_id} was successfully deleted'})
	return jsonify({"message":"Nothing happened"})

@app.route('/profile/<username>', methods=['POST','GET'])
@token_optional
def profile(current_user, username):
	profile = mongo.db.users.find_one_or_404({'username':username})
	if current_user:
		#log_activity(current_user,{'viewed_profile':{username:datetime.datetime.now()}})
		if current_user['username']==username:
			return json_util.dumps({'message':"It's your profile!",'profile':current_user})
	user = mongo.db.users.find_one_or_404({'username':username})
	req = requests.post(request.url_root+'log',data=json_util.dumps({'current_user':current_user,'activity':{'viewed_profile':{username:datetime.datetime.now()}}}))
	print(req.content)
	return json_util.dumps({'profile':user})

@app.route('/log', methods=["POST","GET"])
def log():
	if request.method!="POST":
		return jsonify({'error':"Only POST allowed"})
	print('all data in req = ', request.data)
	data = json_util.loads(request.data)
	print("Data in logs ", data)
	if 'current_user' in data and 'activity' in data and data['current_user'] is not None:
		try:
			log_activity = mongo.db.users.find_one_or_404({'username':data['current_user']['username']})['log_activity']
		except:
			log_activity={}
		log_activity.update(data['activity'])
		mongo.db.users.update_one({'username':data['current_user']['username']},{'$set':{'log_activity':log_activity}})
		return jsonify({'message':f"Action {data['activity']} for {data['current_user']['username']} was logged"})
	return jsonify({"error":"Nothing to log"})