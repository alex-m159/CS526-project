from . import create_app
from flask import render_template
from flask_socketio import SocketIO, emit
from flask_cors import cross_origin
 
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/", methods=['GET'])
def home():
    return render_template('pubhealth/dist/index.html')

@socketio.on('message')
def handle_message():
    print(f'Received socket IO message: ')
    emit('response', {'field': 'value'})

if __name__ == "__main__":
    print("Running socketio")
    socketio.run(app)
