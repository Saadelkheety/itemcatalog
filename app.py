from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Main_Category, Sub_Category

app = Flask(__name__) # instaniate an app

engine = create_engine('sqlite:///database.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
# main page
@app.route("/")
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

# add an item to a main category element
@app.route("/add/", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        newItem = Sub_Category(name=request.form['name'], description=request.form[
                           'description'], main_id=request.form['main_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('index'))
    else:
        main_category = session.query(Main_Category).all()
        return render_template("add.html",main_category=main_category)

# display an Item descriptin
@app.route("/<int:item_id>/item/")
def item(item_id):
    main_category = session.query(Main_Category).all()
    required_item = session.query(Sub_Category).filter_by(id=item_id).first()
    return render_template("item.html",item=required_item,main_category=main_category)

# edit an item details
@app.route("/edit/<int:item_id>/", methods=['GET', 'POST'])
def edit(item_id):
    main_category = session.query(Main_Category).all()
    required_item = session.query(Sub_Category).filter_by(id=item_id).first()
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
    main_category = session.query(Main_Category).all()
    required_item = session.query(Sub_Category).filter_by(id=item_id).first()
    session.delete(required_item)
    session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
