import requests
import json

from bson import json_util 


class Interactions:
	def __init__(self, basic_url):
		self.url = basic_url
		self.token = None

	def login(self):
		username = input("Enter username: ")
		password = input("Enter password: ")
		endpoint = self.url+'/login'
		data = {'username':username,'password':password}
		req = requests.post(endpoint,data=data)
		#print(json_util.loads(req.content))
		self.token = json.loads(req.content)['token']
		print(f"Auth token was set into HEADERS {self.token}")

	def register(self):
		username = input("Enter username: ")
		password = input("Enter password: ")
		confirm = input("Confirm password: ")
		endpoint = self.url+'/register'
		data = {'username':username,'password':password, 'confirm':confirm}
		req = requests.post(endpoint,data=data)
		print(json_util.loads(req.content))

	def logout(self):
		self.token = None
		endpoint = self.url+'/logout'
		req = requests.get(endpoint)
		print(json_util.loads(req.content))

	def view_posts(self):
		headers = {'Content-Type':'application/json','x-access-tokens':self.token}
		print('Working with headers: ', headers)
		req = requests.get(self.url, headers=headers)
		print(json_util.loads(req.content))

	def new_post(self):
		headers = {'Content-Type':'application/json','x-access-tokens':self.token}
		print('Working with headers: ', headers)
		endpoint=f'{self.url}/new_post'
		text = input("Enter post text: ")
		data = {'new_text':text,'add_post':'yep'}
		req = requests.post(endpoint,headers=headers,data=json.dumps(data))
		print(json_util.loads(req.content))

	def reaction(self,action):
		headers = {'Content-Type':'application/json','x-access-tokens':self.token}
		print('Working with headers: ', headers)
		endpoint = self.url+'/like'
		post_id = input('Enter post id: ')
		data = {'like':action,'post':post_id}
		req = requests.post(endpoint,headers=headers,data=json.dumps(data))
		print(json_util.loads(req.content))

	def delete(self, action):
		headers = {'Content-Type':'application/json','x-access-tokens':self.token}
		print('Working with headers: ', headers)
		endpoint = self.url+'/delete'
		post_id = input('Enter post id: ')
		data = {'delete':action,'post_id':post_id}
		req = requests.post(endpoint,headers=headers,data=json.dumps(data))
		print(json_util.loads(req.content))


	def view_profile(self):
		headers = {'Content-Type':'application/json','x-access-tokens':self.token}
		print('Working with headers: ', headers)
		username = input("Enter username: ")
		endpoint = f'{self.url}/profile/{username}'
		req = requests.get(endpoint, headers=headers)
		print(json_util.loads(req.content))


i=0
inter = Interactions('http://127.0.0.1:5000')
while i!='q':
	actions = ['0. logout', '1. login', '2. register', '3. view posts', '4. new post',
	'5. like post', '6. dislike post', '7. view profile', '8. del post by id']
	print("\n__________\n")
	for action in actions:
		print(action)
	i = input("Выберите действие:\n")
	if i=='0':
		inter.logout()
	elif i=='1':
		inter.login()
	elif i=='2':
		inter.register()
	elif i=='3':
		inter.view_posts()
	elif i=='4':
		inter.new_post()
	elif i=='5':
		inter.reaction('like')
	elif i=='6':
		inter.reaction('dislike')
	elif i=='7':
		inter.view_profile()
	elif i=='8':
		inter.delete('post_by_id')
