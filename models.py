from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)
    
    watchlists = db.relationship('Watchlist', backref='user', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.username


class Watchlist(db.Model):
    __tablename__ = "watchlist"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    watchlist_data = db.relationship('WatchlistData', backref='watchlist', lazy=True)

    def __repr__(self):
        return '<Watchlist %r>' % self.name


class WatchlistData(db.Model):
    __tablename__ = "watchlist_data"
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlist.id'), nullable=False)

    def __repr__(self):
        return '<WatchlistData %r>' % self.company_name
