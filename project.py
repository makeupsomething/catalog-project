from flask import (
    Flask,
    render_template,
    request, redirect,
    jsonify,
    url_for,
    flash
)
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from setup_db import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
app = Flask(__name__)


engine = create_engine('sqlite:///categoryanditems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
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
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        login_session['user_id']=createUser(login_session)
    else:
        login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


@app.route('/gdisconnect', methods=['GET', 'POST'])
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
                           params={'token': login_session.get('access_token')},
                           headers={'content-type':
                                    'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/categories/')
def categoryList():
    categories = session.query(Category).all()
    recentlyUpdated = session.query(Item)\
        .order_by(desc(Item.time_created))\
        .limit(3)\
        .all()
    if 'username' not in login_session:
        return render_template(
            'public_categories.html',
            categories=categories,
            updated=recentlyUpdated)
    else:
        return render_template(
                'categories.html',
                categories=categories,
                updated=recentlyUpdated)


@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items')
def category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category_id=category.id)
    if 'username' not in login_session:
        return render_template(
                'public_category.html',
                category=category,
                items=items,
                categories=categories)
    else:
        return render_template(
                'category.html',
                category=category,
                items=items,
                categories=categories)


@app.route('/categories/items/new', methods=['GET', 'POST'])
def AddItem():
    if 'username' not in login_session:
        return redirect(url_for('categoryList'))
    categories = session.query(Category).all()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=request.form['category'],
            user_id=login_session['user_id'])
        cat = request.form['category']
        session.add(newItem)
        session.commit()
        return redirect(url_for(
                        'category',
                        category_id=cat))
    else:
        return render_template('newitem.html', categories=categories)


@app.route('/categories/<int:category_id>/items/new', methods=['GET', 'POST'])
def AddCategoryItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('categoryList'))
    categories = session.query(Category).all()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=category_id,
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for(
                        'category',
                        category_id=category_id))
    else:
        return render_template(
                'newitemcat.html',
                category_id=category_id,
                categories=categories)


@app.route('/categories/<int:category_id>/<int:item_id>',
           methods=['GET', 'POST'])
def item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return render_template(
                'public_item.html',
                category=category,
                item=item,
                categories=categories)
    else:
        return render_template(
                'item.html',
                category=category,
                item=item,
                categories=categories)


@app.route('/categories/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def EditItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    creator = getUserInfo(editedItem.user_id)
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect(url_for('categoryList'))
    if login_session['user_id'] != creator.id:
        flash("You do not have permission to edit this item")
        return redirect(url_for('item', category_id=category_id, item_id=item_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        session.add(editedItem)
        session.commit()
        return redirect(url_for(
                'category',
                category_id=category_id))
    else:
        all_categories = categories
        categories.remove(editedItem.category)
        return render_template(
                'edititem.html',
                category_id=category_id,
                item_id=item_id,
                item=editedItem,
                categories=categories,
                all_categories=all_categories)


@app.route('/categories/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def DeleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('categories'))
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    creator = getUserInfo(itemToDelete.user_id)
    if login_session['user_id'] != creator.id:
        flash("You do not have permission to delete this item")
        return redirect(url_for('item', category_id=category_id, item_id=item_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for(
                'category',
                category_id=category_id))
    else:
        return render_template(
                'deleteitem.html',
                category_id=category_id,
                item_id=item_id,
                item=itemToDelete,
                categories=categories)


@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/categories/<int:category_id>/items/JSON')
def categoryJSON(category_id):
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
