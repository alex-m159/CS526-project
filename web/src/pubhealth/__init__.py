
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__, 
                static_url_path='',
                static_folder='templates/pubhealth/dist')
    app.config['secret'] = 'SECRET!@@21312312429'
    CORS(app)    
    return app