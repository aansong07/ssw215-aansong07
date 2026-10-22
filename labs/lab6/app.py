from flask import Flask, jsonify, render_template, send_from_directory

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
        "title": "Tomato Soup",
        "description": "I want to make a gym workout planner.",
        "likes": 0,
    },
    {
        "id": 3,
        "title": "Creative ideas",
        "description": "I want to make something related to music.",
        "likes": 0,
    },
    {
        # hand-edited by AA
        "id": 4,
        "title": "Recipe Book",
        "description": "I want to make a recipe book app.",
        "likes": 0,
        },
]


@app.route("/")
def index():
    return render_template("index.html", projects=projects_db)


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    return jsonify({"id": project_id, "likes": project["likes"]})


@app.route("/assets/avatar.jpg")
def avatar():
    return send_from_directory("assets", "avatar.jpg")


if __name__ == "__main__":
    app.run(debug=True)
