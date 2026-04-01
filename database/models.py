from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(String(255))
    username = Column(String(255))
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    history = relationship("History", back_populates="user")
    watchlist = relationship("Watchlist", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    comments = relationship("Comment", back_populates="user")

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    year = Column(Integer, default=0)
    genre = Column(String(255))
    lang = Column(String(50), default="uz")
    file_id = Column(String(255), nullable=False)
    media_type = Column(String(50), default="video") # video, photo, document
    content_type = Column(String(50), default="movie") # movie, trailer
    is_series = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    episodes = relationship("Episode", back_populates="movie", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="movie", cascade="all, delete-orphan")
    watchlist = relationship("Watchlist", back_populates="movie", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    episode_number = Column(Integer, nullable=False)
    file_id = Column(String(255), nullable=False)
    
    movie = relationship("Movie", back_populates="episodes")

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    
    user = relationship("User", back_populates="watchlist")
    movie = relationship("Movie", back_populates="watchlist")

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    stars = Column(Integer) # 1-5
    
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")
    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='_user_movie_rating_uc'),)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    text = Column(Text, nullable=False)
    status = Column(String(50), default="pending") # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="comments")
    movie = relationship("Movie", back_populates="comments")

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="history")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id")) # Series subscription
    
class AdChannel(Base):
    __tablename__ = "ad_channels"
    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, unique=True, nullable=False)
    link = Column(String(255), nullable=False)

class BotSetting(Base):
    __tablename__ = "bot_settings"
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=False)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    message = Column(Text, nullable=False)
    answer = Column(Text)
    status = Column(String(50), default="open") # open, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
