# config.py

import os

class Config:
    SECRET_KEY = 'your_secret_key_here'  # Replace with a secure secret key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
