# app.py, main application script
# 2024

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
