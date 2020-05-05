from gevent import monkey
monkey.patch_all()

import redis
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room, rooms


app = Flask(__name__)
db = redis.StrictRedis('localhost', 6379, 0)
socketio = SocketIO(app, ping_timeout=10, ping_interval=5)

connected_members = []

@app.route('/')
def main():
  return render_template('main.html')

@app.route('/invited')
def invited():
  room_id = request.args.get('room_id')
  join_room(room_id)
  return render_template('invited.html', room_id=room_id)

@socketio.on('connect', namespace='/dd')
def ws_conn(*args, **kwargs):
  # c = db.incr('connected')
  # socketio.emit('msg', {'room_id': 100 }, namespace='/dd')
  print(request.sid)
  room_id = rooms()[0]
  socketio.emit('share-link', {'link_url': f'http://127.0.0.1:5000/invited?room_id={room_id}'}, namespace='/dd')
  if not request.sid in connected_members:



@socketio.on('join', namespace='/dd')
def ws_join(room_payload):
  print('join room on sever', room_payload)
  # socketio.emit('msg', {'room_id': 100 }, namespace='/dd')

if __name__ == '__main__':
  socketio.run(app, debug=True)