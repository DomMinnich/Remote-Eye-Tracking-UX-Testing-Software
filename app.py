# Dominic Minnich 2024
# app.py, main application script

from app import create_app
import requests

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
	#domain name public specific ip with port
 #app.run(host="10.100.233.138", port=5000)