"""
Module with user Helper Functions
"""
from app import db_session
from app.ItemCatalog.models import User


def create_user(login_session):
    """
    create new user function in database
    :param login_session:
    :return: user's id
    """
    new_user = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    db_session.add(new_user)
    db_session.commit()
    user = db_session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    """
    get user object function
    :param user_id:
    :return: user object from database
    """
    user = db_session.query(User).filter_by(id=user_id).one()
    return user


def get_user_info_by_session(login_session):
    """
    get user from db by session
    :param login_session:
    :return: user or None
    """
    if 'user_id' in login_session:
        user_id = login_session.get('user_id')
        user = db_session.query(User).filter_by(id=user_id).one()
        return user
    else:
        return None


def get_user_id(email):
    """
    get user id by email
    :param email:
    :return: user's id or None
    """
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None
