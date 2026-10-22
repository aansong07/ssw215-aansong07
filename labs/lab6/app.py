from flask import Flask, render_template


app = Flask(__name__)

projects_db = [
    {
        "id": 1,
        "title": "Java projects",
        "description": "I have made a blackjack simulator in java.",
        "likes": 0,
    },
    {
        "id": 2,
        "title": "Future goals",
        "description": "I want to make a gym workout planner",
        "likes": 0,
    },
    {
        "id": 3,
        "title": "Creative ideas",
        "description": "I want to make something related to music.",
        "likes": 0,
    },
]


@app.route("/")
def index():
    return render_template("index.html", projects_db=projects_db)


if __name__ == "__main__":
    app.run(debug=True)
