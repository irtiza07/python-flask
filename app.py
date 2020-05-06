import uuid

from gevent import monkey
from collections import namedtuple
monkey.patch_all()

from flask import Flask, render_template, request, make_response
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room, rooms, send, emit
from flask_cors import CORS, cross_origin
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment

SoundOverlay = namedtuple('SoundOverlay', ['time_in_seconds', 'overlay_song_title'])

app = Flask(__name__)
cors = CORS(app)
socketio = SocketIO(app)
unique_sessions = set()
room_assignments = {} ## {sid : room_id}
sound_overlays = []

def generate_share_link(admin_sid):
  return f'http://127.0.0.1:5000/invited?room_id={admin_sid}'

def process_song():
  song = AudioSegment.from_wav('./static/backing_track.wav')
  sample_dict = {
    'sound_1': AudioSegment.from_wav('./static/sound_1.wav'),
    'sound_2': AudioSegment.from_wav('./static/sound_2.wav'),
  }
  for overlay in sound_overlays:
    song = song.overlay(
      sample_dict[overlay.overlay_song_title],
      float(overlay.time_in_seconds)*1000
    )
  print("Starting file export")
  song.export("combined.wav", format="wav")
  print("Done exporting file..")

def process_video():
  loops = [VideoFileClip('./static/backing-video.mp4') for i in range(10)]
  audio = AudioFileClip("combined.wav").set_duration(30)
  final_clip = concatenate_videoclips(loops).set_audio(audio)
  final_clip.write_videofile("output.mp4", audio_codec='libvorbis')

@app.route('/')
@cross_origin()
def main():
  response = make_response(render_template('main.html'))
  return response

@app.route('/invited')
@cross_origin()
def invited():
  room_id = request.args.get('room_id')
  response = make_response(render_template('invited.html', room_id=room_id))
  return response

@socketio.on('connect', namespace='/dd')
def ws_conn():
  # socketio.emit('share-link', {'link_url': f'http://127.0.0.1:5000/invited?room_id={room_id}'}, namespace='/dd')
  print("Connected")
  unique_sessions.add(request.sid)

@socketio.on('share-requested', namespace='/dd')
def ws_share_requested():
  print("Share button clicked")
  room_assignments[request.sid] = request.sid # Add user to their own sid room
  return generate_share_link(request.sid)

@socketio.on('share-accepted', namespace='/dd')
def on_join(room_id):
  print("New person joined through share")
  join_room(room_id)
  unique_sessions.add(request.sid)
  room_assignments[request.sid] = room_id
  print(room_assignments)

@socketio.on('game-started', namespace='/dd')
def on_join():
  print("Admin kicked off the game")
  emit('game-started', room=room_assignments[request.sid])

@socketio.on('sample-sound-played', namespace='/dd')
def on_sound_played(sound_payload):
  sound = sound_payload["sound"]
  moment = sound_payload["moment"]
  sound_overlays.append(SoundOverlay(
    time_in_seconds=moment,
    overlay_song_title=sound
  ))

  print(f'Admin played sound {sound} at {moment} of backing track')
  emit('sample-sound-played', {'sound':sound}, room=room_assignments[request.sid])

@socketio.on('game-finish', namespace='/dd')
def on_finish():
  print("Admin kicked off the game")
  emit('game-finish', room=room_assignments[request.sid])
  process_song()
  process_video()


if __name__ == '__main__':
  socketio.run(app, debug=False)