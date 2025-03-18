# Dominic Minnich 2024
# app.py, main application script

from app import create_app
import requests

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
