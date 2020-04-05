from flask import jsonify, Blueprint, request
from datetime import datetime

from application import mongo

api_bpt = Blueprint('api', __name__)


@api_bpt.route('/api/analytics', methods=['POST','GET'])
def analytics():
	if 'date_from' in request.args and 'date_to' in request.args:
		date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
		date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
		message = {'date':'likes_count'}
		for post in mongo.db.posts.find():
			likes_for_post = post['likes_list'].values()
			for date in likes_for_post:
				if date.date()>=date_from and date.date()<=date_to:
					if date.date().strftime('%Y-%m-%d') in message:
						count = int(message[date.date().strftime('%Y-%m-%d')])+1
						message.update({date.date().strftime('%Y-%m-%d'):count})
					else:
						message.update({date.date().strftime('%Y-%m-%d'):1})
		return jsonify(message)


@api_bpt.route('/api/activity/<username>', methods=['POST','GET'])
def activity(username):
	user = mongo.db.users.find_one_or_404({'username':username})
	try:
		activity = user['log_activity']
	except:
		activity = {'log_activity':"Empty"}
	try:		
		last_logged = user['last_logged']
	except:
		last_logged = {'last_logged':"Empty"}
	resp = {'last_logged':last_logged,
	'log_activity':activity}
	return jsonify(resp)