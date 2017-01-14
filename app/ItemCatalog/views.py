"""
Views module
"""
import json, random, string, httplib2, requests

from flask import abort, flash, redirect, render_template, request, url_for, \
    g, jsonify
from flask import make_response
from flask import session as login_session
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from app import app, db_session
from app.ItemCatalog.models import Category, CatalogItem
from app.UserHelper import get_user_id, create_user, get_user_info
from app.app_decorators import login_required, is_category_exists, \
    is_category_owner, is_item_exists, is_item_owner
from config import CLIENT_ID


@app.route('/')
@app.route('/catalog')
def default_page():
    return render_template("main_page.html")


@app.route('/catalog/JSON')
def get_categoriesJSON():
    category = db_session.query(Category).all()
    return jsonify(Category=[c.serialize for c in category])


@app.route('/catalog/<int:category_id>/list')
def catalog_items(category_id):
    category = db_session.query(Category).get(category_id)
    if category:
        context = {'current_category': category}
        return render_template("category_page.html", **context)
    else:
        abort(404)


@app.route('/catalog/<int:category_id>/list/JSON')
@is_category_exists
def catalog_itemsJSON(category_id):
    category = db_session.query(Category).get(category_id)
    items = db_session.query(CatalogItem).filter_by(category=category).all()
    return jsonify(CatalogItem=[i.serialize for i in items])


@app.route('/catalog/new-category', methods=['GET', 'POST'])
@login_required
def create_category():
    if request.method == 'POST':
        category_name = request.form['name']
        if category_name and category_name.strip():
            new_category = Category(name=category_name)
            # new_category.user_id = get_user_info_by_session(login_session).id
            new_category.user_id = g.user.id
            db_session.add(new_category)
            db_session.commit()
            return redirect(url_for('default_page'))
        else:
            context = {'error': "You should input category name",
                       'name': request.form['name']}
            return render_template("new-category.html", **context)
    else:
        return render_template("new-category.html")


@app.route('/catalog/<int:category_id>/new-item', methods=['GET', 'POST'])
@app.route('/catalog/new-item', methods=['GET', 'POST'])
@login_required
def create_item(category_id=None):
    if request.method == 'POST':
        item_title = request.form['title']
        item_description = request.form['description']
        item_category = request.form['category']

        if item_title and item_title.strip() \
                and item_description and item_description.strip():

            new_item = CatalogItem(title=item_title,
                                   description=item_description,
                                   category_id=item_category)

            new_item.user_id = g.user.id

            db_session.add(new_item)
            db_session.commit()
            return redirect(url_for('catalog_items', category_id=item_category))
        else:
            context = {'error': "You should input title, description and "
                                "category",
                       'title': request.form['title'],
                       'description': request.form['description'],
                       'category': request.form['category'], }
            return render_template("new-item.html", **context)
    else:
        if category_id:
            category = db_session.query(Category).get(category_id)
            if category:
                context = {'category': category_id}
                return render_template("new-item.html", **context)
            else:
                abort(404)
        else:
            return render_template("new-item.html")


@app.route('/catalog/<int:category_id>/<int:item_id>')
def get_catalog_item(category_id, item_id):
    category = db_session.query(Category).get(category_id)
    item = db_session.query(CatalogItem).get(item_id)
    if category and item:
        context = {'current_category': category, 'current_item': item, }
        return render_template("item_page.html", **context)
    else:
        abort(404)


@app.route('/catalog/<int:category_id>/<int:item_id>/JSON')
@is_item_exists
def get_catalog_itemJSON(category_id, item_id):
    item = db_session.query(CatalogItem).get(item_id)
    return jsonify(CatalogItem=[item.serialize])


@app.route('/catalog/<int:category_id>/delete-category',
           methods=['GET', 'POST'])
@login_required
@is_category_exists
@is_category_owner
def delete_category(category_id):
    category = db_session.query(Category).get(category_id)
    if category:
        context = {'current_category': category}
    else:
        abort(404)
        return

    if request.method == 'POST':
        delete = request.form['Delete']
        if delete:
            db_session.delete(category)
            db_session.commit()
            return redirect(url_for('default_page'))
    else:
        return render_template("delete-category.html", **context)


@app.route('/catalog/<int:category_id>/edit',
           methods=['GET', 'POST'])
@login_required
@is_category_exists
@is_category_owner
def edit_category(category_id):
    category = db_session.query(Category).get(category_id)
    if category:
        context = {'current_category': category}
    else:
        abort(404)
        return

    if request.method == 'POST':

        category_name = request.form['name']
        if category_name and category_name.strip():

            category.name = category_name
            db_session.commit()
            return redirect(url_for('catalog_items', category_id=category.id))
        else:
            context['error'] = "You should input category name"
            context['name'] = request.form['name']

            return render_template("edit-category.html", **context)

    else:
        return render_template("edit-category.html", **context)


@app.route('/catalog/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
@login_required
@is_item_exists
@is_item_owner
def edit_item(category_id, item_id):
    category = db_session.query(Category).get(category_id)
    item = db_session.query(CatalogItem).get(item_id)
    if category and item:
        context = {'current_category': category, 'current_item': item, }
    else:
        abort(404)
        return

    if request.method == 'POST':

        item_title = request.form['title']
        item_description = request.form['description']
        item_category = request.form['category']

        if item_title and item_title.strip() \
                and item_description and item_description.strip():

            item.title = item_title
            item.description = item_description
            item.category_id = int(item_category)

            db_session.commit()
            return redirect(url_for('get_catalog_item',
                                    category_id=category.id,
                                    item_id=item.id))

        else:
            context[
                'error'] = "You should input title, description and category"
            context['title'] = request.form['title']
            context['description'] = request.form['description']
            context['category'] = request.form['category']

            return render_template("edit-item.html", **context)

    else:
        return render_template("edit-item.html", **context)


@app.route('/catalog/<int:category_id>/<int:item_id>/delete-item',
           methods=['GET', 'POST'])
@login_required
@is_item_exists
@is_item_owner
def delete_item(category_id, item_id):
    category = db_session.query(Category).get(category_id)
    item = db_session.query(CatalogItem).get(item_id)
    if category and item:
        context = {'current_category': category, 'current_item': item, }
    else:
        abort(404)
        return

    if request.method == 'POST':
        delete = request.form['Delete']
        if delete:
            db_session.delete(item)
            db_session.commit()
            return redirect(url_for('catalog_items', category_id=category_id))
    else:
        return render_template("delete-item.html", **context)


# Create anti-forgery state token
@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    user = get_user_info(user_id)
    g.user = user

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        g.user = None

        # response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return render_template("disconnect_page.html",
                               message="Successfully disconnected.")
    else:
        # For whatever reason, the given token was invalid.
        # response = make_response(
        #     json.dumps('Failed to revoke token for given user.', 400))
        # response.headers['Content-Type'] = 'application/json'
        # return response
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        g.user = None

        return render_template("disconnect_page.html",
                               message="Failed to revoke token for given user.")
