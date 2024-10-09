from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey("User.username"))
    content = db.Column(db.Text, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("Chatroom.id"))
    created_by = db.Column(db.DateTime)

class Chatroom(db.Model):
    __tablename__ = 'Chatroom'
    id = db.Column(db.Integer, primary_key=True)
    roomname = db.Column(db.String(24), nullable=False, unique=True)

    author_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    members = db.relationship("User", backref="chatroom", lazy=True, foreign_keys='User.room_joined_id')
    messages = db.relationship("Message", backref="chatroom", lazy=True)

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False, unique=True)
    email = db.Column(db.String(24), nullable=False, unique=True)
    pw_hash = db.Column(db.String(64), nullable=False)

    rooms_created = db.relationship("Chatroom", backref="user", lazy=True, foreign_keys='Chatroom.author_id')
    room_joined_id = db.Column(db.Integer, db.ForeignKey("Chatroom.id"))
    joined_time = db.Column(db.DateTime)
    messages_created = db.relationship("Message", backref="user", lazy=True)

    def __init__(self, username, email, pw_hash):
        self.username = username
        self.email = email
        self.pw_hash = pw_hash

    def __repr__(self):
        return "<User %r>" % self.username
