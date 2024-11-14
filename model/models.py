from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class NewsCount(db.Model):
    news_id = db.Column(db.String, primary_key=True)
    count = db.Column(db.Integer, default=0)
