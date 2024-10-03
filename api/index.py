# TODO: reorder
from flask import Flask, request, jsonify
from pocketbase import PocketBase
from pocketbase.utils import ClientResponseError
import os
import uuid

# Load environment variables
if os.name == 'nt':
    from dotenv import load_dotenv
    load_dotenv()

PB_AUTH_COLLECTION = os.getenv('PB_AUTH_COLLECTION')
PB_FILES_COLLECTION = os.getenv('PB_FILES_COLLECTION')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'superseCretKey73')

# initialise pocketbase
pb = PocketBase(os.getenv('PB_URL'))
if not (d := pb.admins.auth_with_password(
    os.getenv('PB_ADMIN_USERNAME'),
    os.getenv('PB_ADMIN_PASSWORD')
)).is_valid:
    raise RuntimeError('Failed to authenticate with PocketBase')

# the receiver creates a room
# - and readies it
# the sender joins the room
# - and ends it (when done)

@app.route('/')
def app_index():
    return 'hello world'

@app.route('/api/create_room')
def api_create_room():
    auth = pb.collection(PB_AUTH_COLLECTION)
    files = pb.collection(PB_FILES_COLLECTION)

    # create receiver
    secret = str(uuid.uuid4())
    receiver = auth.create({
        "secret": secret
    })

    # create room
    room_key = str(uuid.uuid4())
    room = files.create({
        "room_key": room_key,
        "receiver": receiver.id
    })

    return jsonify({
        'user_id': receiver.id,
        'user_secret': secret,
        'room_id': room.id,
        'room_key': room_key
    })

@app.route('/api/join_room', methods=['POST'])
def api_join_room():
    auth = pb.collection(PB_AUTH_COLLECTION)
    files = pb.collection(PB_FILES_COLLECTION)

    data = request.get_json()
    try:
        room = files.get_one(data.get('room_id'))
    except ClientResponseError as e:
        return jsonify({
            'error': 'room not found'
        }), 404
    # authenticate
    if not data.get('room_key') == getattr(room, 'room_key'):
        return jsonify({
            'error': 'room key incorrect'
        }), 403
    
    # create sender
    secret = str(uuid.uuid4())
    sender = auth.create({
        "secret": secret
    })

    # update room
    files.update(room.id, {
        "sender": sender.id
    })

    return jsonify({
        'user_id': sender.id,
        'user_secret': secret
    })

# dev
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)