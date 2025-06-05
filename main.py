"""
Main entry point for Firebase Functions deployment.
This file is required for Firebase Cloud Functions to run the Flask app.
"""
import os
from flask import Flask
from functions_framework import create_app

# Set environment to production for deployment
os.environ.setdefault("ENVIRONMENT", "production")

# Import the Flask app from our main application
from app import app

# Create the functions framework app
def main(request):
    """Main function for Firebase Cloud Functions"""
    with app.app_context():
        return app(request.environ, lambda *args: None)