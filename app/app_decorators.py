"""
Decorators module
"""
from functools import wraps
from flask import g
from flask import redirect
from flask import render_template
from flask import url_for
from app import db_session
from app.ItemCatalog.models import CatalogItem, Category


def login_required(f):
    """
    ask user to login
    :param f:
    :return:
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('show_login'))
        return f(*args, **kwargs)

    return decorated_function


def is_category_exists(function):
    """
    check user permissions
    :param function:
    :return:
    """
    @wraps(function)
    def wrapper(category_id):

        category = db_session.query(Category).get(category_id)

        if category:
            return function(category_id)
        else:
            return render_template("object_not_exists_error.html",
                                   error="Object does not exist !!!")
    return wrapper


def is_category_owner(function):
    """
    check user permissions
    :param function:
    :return:
    """
    @wraps(function)
    def wrapper(category_id):

        category = db_session.query(Category).get(category_id)

        if category and category.user_id == g.user.id:
            return function(category_id)
        else:
            return render_template("permission_error.html",
                                   error="You are not owner of this object")
    return wrapper


def is_item_exists(function):
    """
    check user permissions
    :param function:
    :return:
    """
    @wraps(function)
    def wrapper(category_id, item_id):

        category = db_session.query(Category).get(category_id)
        item = db_session.query(CatalogItem).get(item_id)

        if category and item:
            return function(category_id, item_id)
        else:
            return render_template("object_not_exists_error.html",
                                   error="Object does not exist !!!")
    return wrapper


def is_item_owner(function):
    """
    check user permissions
    :param function:
    :return:
    """
    @wraps(function)
    def wrapper(category_id, item_id):

        item = db_session.query(CatalogItem).get(item_id)

        if item.user_id == g.user.id:
            return function(category_id, item_id)
        else:
            return render_template("permission_error.html",
                                   error="You are not owner of this object")
    return wrapper