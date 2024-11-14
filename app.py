import json

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

from model import db, NewsCount


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

db.init_app(app)
with app.app_context():
    db.create_all()

with open('credentials/isodApi.json', 'r') as file:
    isod_credentials = json.load(file)


@app.route('/')
def hello_world():
    return 'Hello World!'


visit_counts = {}


@app.route('/track', methods=['GET'])
def track():
    news_id = request.args.get('id')

    if not news_id:
        return jsonify({'error': "No 'news_id' parameter was given."}), 400

    news_counter = NewsCount.query.filter(NewsCount.news_id == news_id).first()
    if news_counter is None:
        comment = NewsCount(
            news_id=news_id,
            count=1,
        )
        db.session.add(comment)
    else:
        news_counter.count = news_counter.count + 1

    db.session.commit()

    return jsonify({'message': 'Success!'}), 200


if __name__ == '__main__':
    app.run(debug=True)
