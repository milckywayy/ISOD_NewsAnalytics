import json
import os
from functools import wraps

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort
from flask_cors import CORS
import logging

from model import db, NewsCount
from usosapi.usosapi import USOSAPISession, USOSAPIAuthorizationError

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


if os.path.exists('config/config.json'):
    with open('config/config.json', 'r') as file:
        app_config = json.load(file)
else:
    with open('config/default_config.json', 'r') as file:
        app_config = json.load(file)

app = Flask(__name__)
app.secret_key = os.environ.get('ISOD_NA_SECRET_KEY', os.urandom(24))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SERVER_NAME'] = f'{app_config["app_host"]}:{app_config["app_port"]}'

CORS(app)

db.init_app(app)
with app.app_context():
    db.create_all()

with open('credentials/usos_api_credentials.json', 'r') as file:
    usosapi_credentials = json.load(file)

usosapi = USOSAPISession(
    usosapi_credentials['api_base_address'],
    usosapi_credentials['consumer_key'],
    usosapi_credentials['consumer_secret'],
    ''
)


def is_logged():
    if 'logged_in' in session:
        return True
    return False


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def is_admin(user_id):
    return user_id in app_config['admin_ids']


@app.route('/')
def index():
    if not is_logged():
        return redirect(url_for('login'))

    if not is_admin(session['user_id']):
        logging.info(f'User {session["name"]} ({session["user_id"]}) has no admin privileges')
        return redirect(url_for('logout'))

    news = NewsCount.query.all()[::-1]

    return render_template('index.html', news=news)


@app.route('/usos_auth')
def usos_auth():
    _, request_url = usosapi.get_auth_url(callback=url_for('login', _external=True))
    return redirect(request_url)


@app.route('/login', methods=['GET'])
def login():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')

    if oauth_token and oauth_verifier:
        try:
            usosapi.authorize(oauth_token, oauth_verifier)
            user_data = usosapi.fetch_from_service(
                'services/users/user',
                fields='id|first_name|last_name'
            )

            session['user_id'] = user_data['id']
            session['name'] = f'{user_data["first_name"]} {user_data["last_name"]}'
            session['logged_in'] = True

            logging.info(f'User {session['name']} ({session['user_id']}) logged in')

            return redirect(url_for('index'))

        except USOSAPIAuthorizationError:
            logging.error('Failed to authorize user')

    return render_template('login.html')


@login_required
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@login_required
@app.route('/hide', methods=['GET'])
def hide():
    title = request.args.get('title')

    if not title:
        return redirect(url_for('index'))

    news_item = NewsCount.query.filter(NewsCount.title == title).first()

    if news_item is not None:
        news_item.show = False
        db.session.commit()

    return redirect(url_for('index'))


@app.route('/track', methods=['GET'])
def track():
    title = request.args.get('title')

    if not title:
        return jsonify({'error': "No 'title' parameter was given."}), 400

    news_counter = NewsCount.query.filter(NewsCount.title == title).first()
    if news_counter is None:
        news_item = NewsCount(
            title=title
        )
        db.session.add(news_item)
    else:
        news_counter.count = news_counter.count + 1

    db.session.commit()

    return jsonify({'message': 'Success!'}), 200


if __name__ == '__main__':
    app.run(debug=True)
