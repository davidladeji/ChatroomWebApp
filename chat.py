import os
import json
import datetime
from flask import Flask, redirect, render_template, request, session, url_for, flash, abort
from models import db, User, Chatroom, Message
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'chat.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(__name__)
app.config.from_envvar('CHAT_SETTINGS', silent=True)


db.init_app(app)


@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	db.create_all()
	print('Initialized the database.')

@app.route("/")
def default():
	if 'user' not in session:
		return redirect(url_for("login"))

	user = User.query.filter_by(username=session['user']).first()

	if user is None:
		return render_template("base.html", user_id=0)
	return render_template("base.html", user_id=user.id)

def get_user_id(username):
	rv = User.query.filter_by(username=username).first()
	return rv.id if rv else None

@app.route("/login", methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		user = User.query.filter_by(username=request.form['username']).first()
		if user is None:
			error = "Invalid Username"
		elif not check_password_hash(user.pw_hash, request.form['pass']):
			error = "Invalid Password"
		else:
			flash('You were successfully Logged In')
			
			# If another account was loogen in,
			# Log them out
			session.pop('user', None)

			session['user'] = user.username

			# Multi-user log in
			if 'users' not in session:
				session['users'] = []
			
			count = session['users'].count(user.id)
			if (count == 0):
				session['users'].append(user.id)
			return redirect(url_for("rooms", user_id=user.id))

	if error is not None:
		flash(error)

	if 'user' not in session:
		return render_template("login.html", error=error)

	user = User.query.filter_by(username=session['user']).first()
	return render_template("login.html", error=error, user_id=user.id)

@app.route("/register", methods=['GET', 'POST'])
def register():
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['email'] or \
				'@' not in request.form['email']:
			error = 'You have to enter a valid email address'
		elif not request.form['pass']:
			error = 'You have to enter a password'
		elif request.form['pass'] != request.form['confirm-pass']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			new_user = User(request.form['username'],request.form['email'], generate_password_hash(request.form['pass']))
			db.session.add(new_user)
			db.session.commit()
			flash('You were successfully registered and can login now')
			return redirect(url_for("login"))
	if error is not None:
		flash(error)

	if 'user' not in session:
		return render_template("register.html", error=error)
	
	user = User.query.filter_by(username=session['user']).first()
	return render_template("register.html", error=error, user_id=user.id)

@app.route("/logout/<int:user_id>")
def logout(user_id):
	flash("You were logged out")
	session.pop('user', None)

	# Multi-user log out
	index = session['users'].index(user_id)
	if index > 0:
		session['users'].pop(index)

	return redirect(url_for("login"))

@app.route("/rooms/<int:user_id>")
def rooms(user_id):
	rooms = Chatroom.query.all()
	length = len(rooms)
	return render_template("rooms.html", rooms=rooms, user_id=user_id, number_of_rooms=length)

@app.route("/create_room/<int:user_id>", methods=['GET', 'POST'])
def create_chat_room(user_id):
	if 'user' not in session:
		abort(404)
	error=None
	if request.method == 'POST':
		room = Chatroom.query.filter_by(roomname=request.form['roomname']).first()
		if not request.form['roomname']:
			error = 'You have to enter a name for the Chat room'
		elif room is not None:
			error = 'A room is already created with this name'
		else:
			# Multi-user 
			user = User.query.filter_by(id=user_id).first()
			#user = User.query.filter_by(username=session['user']).first()
			room = Chatroom(roomname=request.form['roomname'], user=user)

			db.session.add(room)
			db.session.commit()
			flash('You have successfully created a new chat room')
			return redirect(url_for("rooms", user_id=user_id))
	if error is not None:
		flash(error)
	return render_template("roomForm.html", error=error, user_id=user_id)


@app.route("/room_page/<int:user_id>/<int:room_id>")
def room_page(user_id, room_id):

	room = Chatroom.query.filter_by(id=room_id).first()

	# If room gets deleted and they refresh, redirect to rooms
	if room is None:
		return redirect(url_for("rooms", user_id=user_id))
	
	# Multi-user 
	user = User.query.filter_by(id=user_id).first()
	#user = User.query.filter_by(username=session['user']).first()


	joined_time = user.joined_time
	
	room_messages = Message.query.filter_by(room_id=room_id).all()

	old_messages = []
	new_messages = []
	for m in room_messages:
		if m.created_by < joined_time:
			old_messages.append(m)
		else:
			new_messages.append(m)
	return render_template("roomPage.html", user_id=user_id, room=room, old_messages=old_messages, new_messages=new_messages)


@app.route("/join_room/<int:user_id>/<int:room_id>")
def join_chat_room(user_id, room_id):
	if 'user' not in session:
		abort(404)

	room = Chatroom.query.filter_by(id=room_id).first()
	if room is None:
		abort(404)
	
	# Multi-user
	user = User.query.filter_by(id=user_id).first()
	#user = User.query.filter_by(username=session['user']).first()

	count = room.members.count(user)
	
	if (count == 0):
		room.members.append(user)
		user.joined_time = datetime.datetime.now()
		db.session.commit()
	
	return redirect(url_for("room_page", user_id=user_id, room_id=room_id))

@app.route("/leave_room/<int:user_id>/<int:room_id>")
def leave_chat_room(user_id, room_id):
	if 'user' not in session:
		abort(404)
	
	room = Chatroom.query.filter_by(id=room_id).first()
	if room is None:
		abort(404)
	
	# Multi-user
	user = User.query.filter_by(id=user_id).first()
	#user = User.query.filter_by(username=session['user']).first()

	index = room.members.index(user)
	room.members.pop(index)
	db.session.commit()
	return redirect(url_for("rooms", user_id=user.id))


@app.route("/delete_room/<int:user_id>/<int:room_id>")
def delete_chat_room(user_id, room_id):
	room = Chatroom.query.filter_by(id=room_id).first()

	if user_id != room.author_id:
		abort(404)
	
	db.session.delete(room)

	db.session.commit()
	flash('You have successfully delted a chat room')
	return redirect(url_for("room_page", user_id=user_id, room_id=room_id))

@app.route("/clear_chat/<int:user_id>/<int:room_id>")
def clear_chat(user_id, room_id):
	room = Chatroom.query.filter_by(id=room_id).first()

	for m in room.messages:
		db.session.delete(m)

	db.session.commit()
	return redirect(url_for("room_page", user_id=user_id, room_id=room_id))


@app.route("/post_message/<int:user_id>", methods=["POST"])
def post_message(user_id):
	user = User.query.filter_by(id=user_id).first()
	room = Chatroom.query.filter_by(id=user.room_joined_id).first()
	msg = Message(content=request.form["message"], user=user, chatroom=room)
	msg.created_by = datetime.datetime.now()
	db.session.add(msg)
	db.session.commit()

	joined_time = user.joined_time
	room_messages = Message.query.filter_by(room_id=room.id).all()
	new_messages = []

	for m in room_messages:
		if m.created_by >= joined_time:
			new_messages.append([m.author, m.content])

	return json.dumps(new_messages)

@app.route("/messages/<int:user_id>")
def get_messages(user_id):
	user = User.query.filter_by(id=user_id).first()
	room = Chatroom.query.filter_by(id=user.room_joined_id).first()
	user_join_time = user.joined_time
	new_messages = []

	for m in room.messages:
		if m.created_by >= user_join_time:
			message_obj = [m.author, m.content]
			new_messages.append(message_obj)

	return json.dumps(new_messages)

@app.route("/get_room_exists/<int:room_id>")
def get_room_exists(room_id):
	room = Chatroom.query.filter_by(id=room_id).first()
	
	returnMsg = -1
	if room is None:
		returnMsg = 0
	else:
		returnMsg = 1

	return json.dumps(returnMsg)