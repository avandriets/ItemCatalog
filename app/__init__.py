"""
App module settings
"""
import random
import string

from flask import Flask, render_template, g
from flask import abort
from flask import request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import session as login_session

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')


# init csrf protection
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = login_session.pop('_csrf_token', None)

        token_form = request.form.get('_csrf_token')
        token_header = request.headers.get('X-CSRFToken')

        if token_header:
            check_token = token_header
        else:
            check_token = token_form

        if not token or token != check_token:
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in login_session:
        random_str = ''.join(random.choice(string.ascii_uppercase +
                                           string.digits)
                             for x in xrange(32))
        login_session['_csrf_token'] = random_str
    return login_session['_csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token
# @app.context_processor
# def csrf_token():
#     """
#     inject site name in context
#     :return:
#     """
#     return {'csrf_token': generate_csrf_token}


# prepare for creating db
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'],
                       convert_unicode=True)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

from ItemCatalog import models

Base.metadata.create_all(bind=engine)

from ItemCatalog import views


# HTTP error handling
@app.errorhandler(404)
def not_found(error):
    """
    Simple 404 page
    :param error:
    :return:
    """
    return render_template('404.html'), 404


@app.before_request
def load_user():
    from flask import session as login_session
    from app.UserHelper import get_user_info

    if 'user_id' in login_session:
        user_id = login_session.get('user_id')
        user = get_user_info(user_id)
    else:
        user = None

    g.user = user


@app.context_processor
def site_name():
    """
    inject site name in context
    :return:
    """
    return {'site_name': app.config['SITE_NAME']}


@app.context_processor
def inject_user():
    """
    inject user object in context

    :return:
    """
    # from flask import session as login_session
    # from app.UserHelper import get_user_info
    #
    # if 'user_id' in login_session:
    #     user_id = login_session.get('user_id')
    #     return {'user': get_user_info(user_id)}
    # else:
    #     return {'user': None}
    return {'user': g.user}


@app.context_processor
def inject_categories_list():
    """
    inject categories list in context
    :return:
    """
    categories = db_session.query(models.Category).all()
    return {'categories': categories}


@app.context_processor
def inject_items_list():
    """
    inject items list to context
    :return:
    """

    def items_list(category_parameter):
        if category_parameter:
            return db_session.query(models.CatalogItem).filter_by(
                category=category_parameter)
        else:
            return db_session.query(models.CatalogItem).limit(10).all()

    return {'items': items_list}


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
