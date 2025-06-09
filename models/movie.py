from sqlalchemy import Column, Integer, String, Float, Text
from database.db import db
from sqlalchemy.orm import relationship
import json

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)  # ID TMDB
    title = db.Column(db.String(255), nullable=False)
    overview = db.Column(db.Text, nullable=True)
    poster_path = db.Column(db.String(255), nullable=True)
    genres = db.Column(db.JSON, nullable=True)  # Stocké en JSON string
    popularity = db.Column(db.Float, nullable=True)
    release_date = db.Column(db.String(20), nullable=True)

    # Relations
    comments = db.relationship(
        'Comment', 
        backref=db.backref('movie', lazy='joined'),
        lazy=True, 
        cascade="all, delete-orphan"
    )
    
    likes = db.relationship(
        'Like', 
        backref='movie', 
        lazy=True, 
        cascade="all, delete-orphan"
    )
    
    watchlist_items = db.relationship(
        'Watchlist',
        backref='movie',
        lazy=True,
        cascade="all, delete-orphan",
        overlaps="watchlists"
    )

    def __repr__(self):
        return f'<Movie {self.title}>'

    def to_dict(self):
        if isinstance(self.genres, str):
            genres = json.loads(self.genres) if self.genres else []
        else:
            genres = self.genres if self.genres else []
        return {
            'id': self.id,
            'title': self.title,
            'overview': self.overview,
            'poster_path': self.poster_path,
            'genres': self.genres if isinstance(self.genres, list) else json.loads(self.genres),
            'popularity': self.popularity,
            'release_date': self.release_date,

        }