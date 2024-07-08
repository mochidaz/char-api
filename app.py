from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
import hashlib
import random

from werkzeug.utils import secure_filename

from flask import send_from_directory

app = Flask(__name__, static_url_path='/media', static_folder='media')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'media'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
app.app_context().push()

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.String(255), nullable=False)

    def __init__(self, name, description, image_url, user_id):
        self.name = name
        self.description = description
        self.image_url = image_url
        self.user_id = user_id

class CharacterSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Character

character_schema = CharacterSchema()
characters_schema = CharacterSchema(many=True)

@app.route('/character', methods=['POST'])
def add_character():
    user_id = request.headers.get('Authorization')
    print(user_id)
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authorization header missing",
            "data": None,
        }), 401

    name = request.form['name']
    description = request.form['description']
    image = request.files['image']

    if image:
        filename = hashlib.md5(random.getrandbits(128).to_bytes(16, 'big')).hexdigest() + secure_filename(image.filename)
        image_path = os.path.join('media', filename)
        image.save(image_path)
    else:
        return jsonify({
            "status": "error",
            "message": "Image missing",
            "data": None,
        }), 400

    new_character = Character(name=name, description=description, image_url=image_path, user_id=user_id)
    db.session.add(new_character)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Character added successfully",
        "data": None,
    }), 201

@app.route('/character', methods=['GET'])
def get_characters():
    all_characters = Character.query.all()
    result = characters_schema.dump(all_characters)
    return jsonify({
        "status": "success",
        "message": "Characters retrieved successfully",
        "data": result,
    }), 200

@app.route('/character/<id>', methods=['GET'])
def get_character(id):
    character = Character.query.get(id)
    return jsonify({
        "status": "success",
        "message": "Character retrieved successfully",
        "data": character_schema.dump(character),
    }), 200

@app.route('/character/user/<user_id>', methods=['GET'])
def get_character_by_user(user_id):
    character = Character.query.filter_by(user_id=user_id)
    return jsonify({
        "status": "success",
        "message": "Characters retrieved successfully",
        "data": characters_schema.dump(character),
    }), 200

@app.route('/character/<id>', methods=['PATCH'])
def update_character(id):
    user_id = request.headers.get('Authorization')
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authorization header missing",
            "data": None,
        }), 401

    character = Character.query.get(id)
    if not character or character.user_id != user_id:
        return jsonify({
            "status": "error",
            "message": "Unauthorized",
            "data": None,
        }), 403

    name = request.form.get('name', character.name)
    description = request.form.get('description', character.description)
    image_file = request.files.get('image')

    character.name = name
    character.description = description
    
    if image_file:
        filename = hashlib.md5(random.getrandbits(128).to_bytes(16, 'big')).hexdigest() + secure_filename(image_file.filename)
        image_path = os.path.join('media', filename)
        image_file.save(image_path)
        character.image_url = image_path

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Character updated successfully",
        "data": None,
    }), 200

@app.route('/character/<id>', methods=['DELETE'])
def delete_character(id):
    user_id = request.headers.get('Authorization')
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authorization header missing",
            "data": None,
        }), 401

    character = Character.query.get(id)
    if not character or character.user_id != user_id:
        return jsonify({
            "status": "error",
            "message": "Unauthorized",
            "data": None,
        }), 403

    db.session.delete(character)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Character deleted successfully",
        "data": None,
    }), 200

@app.get('/media/<filename>')
def get_media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="8181")
