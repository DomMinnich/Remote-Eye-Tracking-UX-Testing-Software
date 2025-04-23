# Dominic Minnich 2024
# app.py, main application script

from app import create_app, db
import requests

app = create_app()

# At the end of app.py
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create all tables before running the app
    app.run(debug=True)
	#domain name public specific ip with port
 #app.run(host="10.100.233.138", port=5000)

