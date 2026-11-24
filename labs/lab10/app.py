import json
import os
import sqlite3

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from ai_service import (
    ProviderRefusalError,
    ProviderUnavailableError,
    extract_project,
    get_github_session,
    remove_github_session,
    refine_github_session,
    start_github_session,
)
from github_service import (
    GitHubUnavailableError,
    ReadmeTooShortError,
    RepositoryNotFoundError,
    fetch_readme,
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    projects = db.relationship("Project", backref="author")


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False, default="")
    summary = db.Column(db.Text, nullable=False, default="")
    technologies = db.Column(db.Text, nullable=False, default="")
    difficulty = db.Column(db.String(20), nullable=False, default="Beginner")
    likes = db.Column(db.Integer, nullable=False, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "technologies": [
                technology.strip()
                for technology in self.technologies.split(",")
                if technology.strip()
            ],
            "difficulty": self.difficulty,
            "likes": self.likes,
            "author_id": self.author_id,
            "author_name": self.author.name,
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

    author = Author(name="Akosua Ansong")
    db.session.add(author)
    for project in projects:
        db.session.add(
            Project(
                id=project["id"],
                title=project["title"],
                description=project["description"],
                summary=project["description"],
                technologies="",
                likes=project["likes"],
                author=author,
            )
        )

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def ensure_project_columns():
    database_path = os.path.join(app.instance_path, "portfolio.db")
    connection = sqlite3.connect(database_path)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(project)")
        }
        if "summary" not in columns:
            connection.execute(
                "ALTER TABLE project ADD COLUMN summary TEXT NOT NULL DEFAULT ''"
            )
        if "technologies" not in columns:
            connection.execute(
                "ALTER TABLE project ADD COLUMN technologies TEXT NOT NULL DEFAULT ''"
            )
        if "difficulty" not in columns:
            connection.execute(
                "ALTER TABLE project ADD COLUMN difficulty "
                "TEXT NOT NULL DEFAULT 'Beginner'"
            )
        connection.execute(
            "UPDATE project SET summary = description "
            "WHERE summary = '' OR summary IS NULL"
        )
        connection.commit()
    finally:
        connection.close()


@app.route("/")
def index():
    projects_db = [project.to_dict() for project in Project.query.all()]
    return render_template("index.html", projects=projects_db)


@app.route("/api/projects")
def get_projects():
    projects_db = [project.to_dict() for project in Project.query.all()]
    return jsonify(projects_db), 200


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

    author = Author.query.first()
    if author is None:
        return jsonify({"error": "Unable to create project"}), 400

    project = Project(title=title, description="", likes=0, author=author)
    db.session.add(project)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to create project"}), 400

    return jsonify(project.to_dict()), 201


@app.route("/api/projects/smart", methods=["POST"])
def smart_create_project():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Notes are required"}), 400

    notes = data.get("notes")
    if not isinstance(notes, str) or len(notes.strip()) < 20:
        return jsonify({"error": "Notes must be at least 20 characters"}), 400

    try:
        extracted = extract_project(notes.strip())
    except ProviderRefusalError as error:
        return jsonify({"error": str(error)}), 422
    except ProviderUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    title = extracted.title.strip()
    summary = extracted.summary.strip()
    if not title or len(title) > 120:
        return jsonify({"error": "The provider returned an invalid title"}), 422

    author = Author.query.first()
    if author is None:
        return jsonify({"error": "Unable to create project"}), 400

    project = Project(
        title=title,
        description=summary,
        summary=summary,
        technologies=", ".join(extracted.technologies),
        likes=0,
        author=author,
    )
    db.session.add(project)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to create project"}), 400

    return jsonify(project.to_dict()), 201


@app.route("/api/projects/git-start", methods=["POST"])
def start_github_import():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A repository owner and name are required"}), 400

    owner = data.get("owner")
    repo = data.get("repo")
    if (
        not isinstance(owner, str)
        or not owner.strip()
        or not isinstance(repo, str)
        or not repo.strip()
    ):
        return jsonify({"error": "A repository owner and name are required"}), 400

    try:
        readme = fetch_readme(owner.strip(), repo.strip())
    except RepositoryNotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ReadmeTooShortError as error:
        return jsonify({"error": str(error)}), 400
    except GitHubUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    try:
        session_id, draft = start_github_session(readme)
    except ProviderRefusalError as error:
        return jsonify({"error": str(error)}), 422
    except ProviderUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    return jsonify({"session_id": session_id, "draft": draft}), 201


@app.route("/api/projects/git-refine", methods=["POST"])
def refine_github_import():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A session ID and feedback are required"}), 400

    session_id = data.get("session_id")
    if not isinstance(session_id, str) or get_github_session(session_id) is None:
        return jsonify({"error": "Draft session not found"}), 404

    feedback = data.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        return jsonify({"error": "Feedback is required"}), 400

    try:
        draft = refine_github_session(session_id, feedback.strip())
    except ProviderRefusalError as error:
        return jsonify({"error": str(error)}), 422
    except ProviderUnavailableError as error:
        return jsonify({"error": str(error)}), 503

    if draft is None:
        return jsonify({"error": "Draft session not found"}), 404

    return jsonify({"draft": draft}), 200


@app.route("/api/projects/git-commit", methods=["POST"])
def commit_github_import():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A session ID is required"}), 400

    session_id = data.get("session_id")
    session = get_github_session(session_id) if isinstance(session_id, str) else None
    if session is None:
        return jsonify({"error": "Draft session not found"}), 404

    draft = session["draft"]
    author = Author.query.first()
    if author is None:
        return jsonify({"error": "Unable to save project"}), 400

    project = Project(
        title=draft.title.strip(),
        description=draft.summary.strip(),
        summary=draft.summary.strip(),
        technologies=", ".join(draft.technologies),
        difficulty=draft.difficulty,
        likes=0,
        author=author,
    )
    db.session.add(project)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to save project"}), 400

    remove_github_session(session_id)
    return jsonify(project.to_dict()), 201


@app.route("/assets/avatar.jpg")
def avatar():
    return send_from_directory("assets", "avatar.jpg")


with app.app_context():
    db.create_all()
    ensure_project_columns()
    init_seed_data()


if __name__ == "__main__":
    app.run(debug=True)
