from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Main_Category, Sub_Category, User, ItemPicture
from sqlalchemy_imageattach.context import store_context
from sqlalchemy_imageattach.stores.fs import HttpExposedFileSystemStore
from sqlalchemy_imageattach.context import (pop_store_context,
                                            push_store_context)
import os
# New imports for anti-forgery
from flask import session as login_session #  this object works as a dict
# we can store values in it for longevity of a user session with our server
import random, string

# imports to handle the code sent back from the callback method for google
# sign in
# to create a flow object from the clientssecrets JSON file
from oauth2client.client import flow_from_clientsecrets
# We will use this method if we run into an error trying to exchange
# an authorization code for an access token. We can use this
# FlowExchangeError method to catch it.
from oauth2client.client import FlowExchangeError
# requests is an Apache 2.0 licensed HTTP library written in
# Python similar to urllib2, but with a few improvements.
import httplib2, json, requests
# this method converts the return value from a function
# into a real response object.
from flask import make_response

app = Flask(__name__) # instaniate an app
store = HttpExposedFileSystemStore('itemimages', '/itemimages')
app.wsgi_app = store.wsgi_middleware(app.wsgi_app)

engine = create_engine('sqlite:///database.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# declare the client ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# server-side function that accepts post requests for google plus login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # verify state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code (collect the one time code from my server)
    code = request.data

    try:
        # use this one time code and exchange it for a credentials object which will contain the access token for my server.
        # Upgrade the authorization code into a credentials object
        # this line creates an oauth flow object and adds my client's secret key information to it.
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        # Here I specify with post message that this is the one time code flow my server will be sending off
        oauth_flow.redirect_uri = 'postmessage'
        # This step_2_exchange function of the flow class exchanges an authorization code for a credentials object.
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
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
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    return output


# User helper Functions
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


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# main page
@app.route("/")
@app.route("/home")
def index():
    main_category = session.query(Main_Category).all()
    latest_items = session.query(Sub_Category).order_by(Sub_Category.id.desc()).limit(10).all()
    return render_template("index.html", main_category=main_category, latest_items=latest_items)

# display the items of a main category
@app.route("/<int:main_id>/items/")
def sub(main_id):
    items = session.query(Sub_Category).filter_by(main_id=main_id).all()
    count = session.query(Sub_Category).filter_by(main_id=main_id).count()
    main_category = session.query(Main_Category).all()
    return render_template("items.html", main_category=main_category, items=items, main_id=main_id, count=count)
'''
# add a picture to an item
def set_item_picture(request, item_id):
    try:
        item = session.query(Sub_Category).get(int(item_id))
        with store_context(store):
            item.picture.from_file(request.files['img'])
            session.commit()
    except Exception:
        session.rollback()
        raise
'''

# add an item to a main category element
@app.route("/add/", methods=['GET', 'POST'])
def add():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Sub_Category(name=request.form['name'], description=request.form[
                           'description'], main_id=request.form['main_id'], user_id=login_session['user_id'])

        if 'img' not in request.files:
            session.add(newItem)
            session.commit()
        else:
            try:
                with store_context(store):
                    newItem.picture.from_file(request.files['img'])
                    session.add(newItem)
                    session.commit()
            except Exception:
                raise
        return redirect(url_for('index'))
    else:
        main_category = session.query(Main_Category).all()
        return render_template("add.html",main_category=main_category)

# display an Item descriptin
@app.route("/<int:item_id>/item/")
def item(item_id):
    main_category = session.query(Main_Category).all()
    required_item = session.query(Sub_Category).filter_by(id=item_id).first()
    creator = session.query(User).filter_by(id=required_item.user_id).first()
    if required_item.picture:
        with store_context(store):
            picture_url = required_item.picture.locate()
    else:
        picture_url = 'none'
    return render_template("item.html",item=required_item,main_category=main_category, picture_url=picture_url, creator=creator)

# edit an item details
@app.route("/edit/<int:item_id>/", methods=['GET', 'POST'])
def edit(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    main_category = session.query(Main_Category).all()
    required_item = session.query(Sub_Category).filter_by(id=item_id).first()
    if required_item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        required_item.name = request.form['name']
        required_item.description = request.form['description']
        session.add(required_item)
        session.commit()
        return redirect(url_for('item',item_id=required_item.id))
    else:
        return render_template("edit.html",item=required_item,main_category=main_category)


# delete an item
@app.route("/<int:item_id>/del/", methods=['POST'])
def delete(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    main_category = session.query(Main_Category).all()
    required_item = session.query(Sub_Category).filter_by(id=item_id).first()
    if required_item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()'>"
    push_store_context(store)
    session.delete(required_item)
    session.commit()
    pop_store_context()
    return redirect(url_for('index'))

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        login_session['loged'] = False
        return redirect(url_for('index'))
    else:
        flash("You were not logged in")
        return redirect(url_for('index'))

# Api end_point
@app.route('/items/JSON')
def itemsJSON():
    items = session.query(Sub_Category).all()
    jsonify(items=[r.serialize for r in items])
    return jsonify(items=[r.serialize for r in items])

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
