from flask import Flask
import psycopg2

app = Flask(__name__)

DB_HOST = "localhost"
DB_NAME = ""
DB_USER = "postgres"
DB_PASSWORD = "@Centivien05"


@app.route('/')
def home():
    return "File Integrity System is Running!"

if __name__ == "__main__":
    app.run(debug=True)
