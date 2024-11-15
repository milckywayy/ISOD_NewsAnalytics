from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class NewsCount(db.Model):
    title = db.Column(db.String, primary_key=True)
    count = db.Column(db.Integer, default=1)
    show = db.Column(db.Boolean, default=True)
