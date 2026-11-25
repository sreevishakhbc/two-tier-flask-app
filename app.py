import os
import MySQLdb
from flask import Flask, request, redirect, render_template

app = Flask(__name__)


def get_db():
    return MySQLdb.connect(
        host=os.environ["MYSQL_HOST"],
        user=os.environ["MYSQL_USER"],
        passwd=os.environ["MYSQL_PASSWORD"],
        db=os.environ["MYSQL_DB"]
    )


@app.route("/", methods=["GET", "POST"])
def home():
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message VARCHAR(255) NOT NULL
            )
        """)

        if request.method == "POST":
            message = request.form.get("message", "").strip()

            if 0 < len(message) <= 255:
                cursor.execute(
                    "INSERT INTO messages (message) VALUES (%s)",
                    (message,)
                )
                db.commit()

            return redirect("/")

        cursor.execute(
            "SELECT message FROM messages ORDER BY id DESC"
        )

        messages = cursor.fetchall()

        return render_template(
            "index.html", messages=messages
        )

    finally:
        cursor.close()
        db.close()


@app.route("/health")
def health():
    try:
        db = get_db()
        db.close()
        return {"status": "healthy"}, 200
    except Exception:
        return {"status": "unhealthy"}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
