import json
import os

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False, default="")
    likes = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "likes": self.likes,
        }


def init_seed_data():
    if Project.query.first() is not None:
        return

    seed_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "projects_seed.json",
    )
    with open(seed_file, "r", encoding="utf-8") as projects_file:
        projects = json.load(projects_file)

    for project in projects:
        db.session.add(
            Project(
                id=project["id"],
                title=project["title"],
                description=project["description"],
                likes=project["likes"],
            )
        )

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise


@app.route("/")
def index():
    projects = Project.query.order_by(Project.id).all()
    return render_template("index.html", projects=projects)


@app.route("/api/projects")
def get_projects():
    projects = Project.query.order_by(Project.id).all()
    return jsonify([project.to_dict() for project in projects]), 200


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project.likes += 1
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to save the upvote"}), 400

    return jsonify({"id": project_id, "likes": project.likes})


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A project title is required"}), 400

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "A project title is required"}), 400

    title = title.strip()
    if len(title) > 120:
        return jsonify({"error": "Project titles must be 120 characters or fewer"}), 400

    project = Project(title=title, description="", likes=0)
    db.session.add(project)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to create project"}), 400

    return jsonify(project.to_dict()), 201


@app.route("/assets/avatar.jpg")
def avatar():
    return send_from_directory("assets", "avatar.jpg")


with app.app_context():
    db.create_all()
    init_seed_data()


if __name__ == "__main__":
    app.run(debug=True)
