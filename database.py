from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy object
db = SQLAlchemy()

# Define the table (model) to log emotions
class EmotionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.Text, nullable=False)
    detected_emotion = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
