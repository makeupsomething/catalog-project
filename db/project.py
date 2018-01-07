from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_db import Base, Category, Item

app = Flask(__name__)


engine = create_engine('sqlite:///categoryanditems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/categories/')
def categoryList():
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/<int:category_id>/')
def category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    return render_template('category.html', category=category, items=items)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)