from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Obtenir les chemins absolus pour les différents dossiers
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
frontend_path = os.path.join(os.path.dirname(basedir), 'frontend')

# S'assurer que le dossier instance existe
os.makedirs(instance_path, exist_ok=True)

# Initialiser l'application Flask
app = Flask(__name__, static_folder=frontend_path)

# Configuration de la base de données
db_path = os.path.join(instance_path, 'chess.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Activer le débogage CORS pour le développement
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

db = SQLAlchemy(app)

# Modèle Participant
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'section': self.section,
            'registration_date': self.registration_date.isoformat()
        }

# Créer la base de données
def create_tables():
    with app.app_context():
        db.create_all()

# Routes API
@app.route('/api/participants', methods=['GET'])
def get_participants():
    participants = Participant.query.all()
    return jsonify([p.to_dict() for p in participants])

@app.route('/api/participants', methods=['POST'])
def add_participant():
    data = request.get_json()
    print("Received data:", data)  # Debug log
    if not data or 'name' not in data or 'section' not in data:
        return jsonify({'error': 'Données invalides'}), 400
    
    participant = Participant(name=data['name'], section=data['section'])
    db.session.add(participant)
    db.session.commit()
    return jsonify(participant.to_dict()), 201

@app.route('/api/participants/<int:participant_id>', methods=['DELETE'])
def delete_participant(participant_id):
    participant = Participant.query.get(participant_id)
    if participant is None:
        return jsonify({'error': 'Participant non trouvé'}), 404
    
    db.session.delete(participant)
    db.session.commit()
    return jsonify({'message': f'Participant {participant_id} supprimé'}), 200

@app.route('/api/participants', methods=['DELETE'])
def clear_participants():
    try:
        db.session.query(Participant).delete()
        db.session.commit()
        return jsonify({'message': 'Tous les participants ont été supprimés'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour servir le frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(frontend_path, path)):
        return send_from_directory(frontend_path, path)
    else:
        return send_from_directory(frontend_path, 'index.html')

if __name__ == '__main__':
    # Créer les tables avant de démarrer le serveur
    create_tables()
    app.run(debug=True)