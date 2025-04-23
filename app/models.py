# models.py
import uuid
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship, backref  # Make sure backref is imported

db = SQLAlchemy()
mail = Mail()


# Association Table: User <-> Project (Collaborators)
class Collaborator(db.Model):
    __tablename__ = "collaborator"
    user_id = db.Column(
        db.String(36), db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    project_id = db.Column(
        db.String(36), db.ForeignKey("project.id", ondelete="CASCADE"), primary_key=True
    )
    # Roles: 'creator', 'co-owner', 'editor', 'viewer'
    role = db.Column(db.String(50), nullable=False, default="viewer")

    # Relationships
    user = relationship("User", back_populates="collaborations")
    project = relationship("Project", back_populates="collaborators")

    def __repr__(self):
        return f"<Collaborator user='{self.user.username if self.user else self.user_id}' project='{self.project.name if self.project else self.project_id}' role='{self.role}'>"


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(
        db.String(192), nullable=False
    )  # Increased length for stronger hashes
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    # Consider using an Enum for roles if complexity increases
    role = db.Column(
        db.String(20), default="student", nullable=False, index=True
    )  # Roles: student, project_manager, admin
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    calibrated = db.Column(db.Boolean, default=False, nullable=False)
    picture = db.Column(
        db.String(100), nullable=True, default="images/pic.png"
    )  # Default picture filename
    config = db.Column(db.JSON, nullable=True)  # User-specific settings JSON
    email_opt_in = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    collaborations = relationship(
        "Collaborator",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    # Relationship to TaskTime (reviews submitted by the user)
    submitted_reviews = relationship("TaskTime", back_populates="user", lazy="dynamic")

    def set_password(self, password):
        # Using stronger hashing method and salt length
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Helper properties using the relationship
    @property
    def owned_projects(self):
        # Using the relationship is generally cleaner
        return (
            Project.query.join(Collaborator)
            .filter(Collaborator.user_id == self.id, Collaborator.role == "creator")
            .order_by(Project.created_at.desc())
            .all()
        )  # Added ordering

    @property
    def accessible_project_ids(self):
        # Returns a set of project IDs the user can access
        return {collab.project_id for collab in self.collaborations.all()}

    @property
    def shared_with_me_projects(self):
        # Using the relationship is cleaner
        return (
            Project.query.join(Collaborator)
            .filter(Collaborator.user_id == self.id, Collaborator.role != "creator")
            .order_by(Project.created_at.desc())
            .all()
        )  # Added ordering

    def get_role_for_project(self, project_id):
        collab = self.collaborations.filter_by(project_id=project_id).first()
        return collab.role if collab else None

    def can_edit_project(self, project_id):
        role = self.get_role_for_project(project_id)
        # Admins can edit all projects
        return role in ["creator", "co-owner", "editor"] or self.role == "admin"

    def can_delete_project(self, project_id):
        role = self.get_role_for_project(project_id)
        # Admins can delete all projects
        return role == "creator" or self.role == "admin"

    def can_manage_collaborators(self, project_id):
        role = self.get_role_for_project(project_id)
        # Admins can manage all collaborators
        return role in ["creator", "co-owner"] or self.role == "admin"

    def __repr__(self):
        return f"<User {self.id[:8]} {self.username} ({self.role})>"


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    name = db.Column(db.String(150), nullable=False, default="Untitled Project")
    link = db.Column(db.String(300), unique=True, nullable=False)  # Figma link
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    eol_time = db.Column(db.DateTime, nullable=False)  # Calculated on creation
    max_submissions = db.Column(db.Integer, nullable=False)  # Set based on creator role
    num_pauses = db.Column(db.Integer, nullable=False, default=0)  # Future use?
    benchmarked = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Relationships
    collaborators = relationship(
        "Collaborator",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Relationship to ALL tasks associated with the project (both major and minor)
    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",
        # Example order: Major tasks first (parent_id is NULL), then by their order. Minor tasks follow.
        order_by="Task.parent_id.nullsfirst(), Task.order",
    )

    # Specific relationship to only MAJOR tasks (parent_id is NULL)
    major_tasks = relationship(
        "Task",
        primaryjoin="and_(Project.id == Task.project_id, Task.parent_id == None)",  # Filter for parent_id IS NULL
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Task.order",  # Order major tasks by their order field
    )

    task_times = relationship(
        "TaskTime",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    @property
    def creator(self):
        # Fetch the user object directly
        creator_collab = self.collaborators.filter_by(role="creator").first()
        return creator_collab.user if creator_collab else None

    def __repr__(self):
        return f"<Project {self.id[:8]} Name: {self.name}>"


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.String(36),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(255), nullable=False)
    order = db.Column(
        db.Integer, nullable=False, default=0
    )  # Order within the project OR among siblings

    # --- Add Parent/Child Relationship ---
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("task.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # Nullable for major tasks

    # Relationship to access child tasks (minor tasks)
    children = relationship(
        "Task",
        # Specify the back reference to access the parent task easily
        # Use backref from sqlalchemy.orm
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",  # Delete children if parent is deleted
        lazy="dynamic",  # Load children only when accessed
    )
    # --- End Parent/Child Relationship ---

    # Relationships
    project = relationship("Project", back_populates="tasks")
    # Relationship to TaskTime (if a TaskTime entry corresponds to one specific Task)
    # If TaskTime just stores the name, this relationship might not be needed directly here.
    # Example: task_time_entries = relationship("TaskTime", back_populates="task", lazy='dynamic')

    # Helper property to easily distinguish (optional but useful)
    @property
    def is_major_task(self):
        return self.parent_id is None

    def __repr__(self):
        parent_info = f" Parent: {self.parent_id}" if self.parent_id else " (Major)"
        return f"<Task {self.id} Proj: {self.project_id[:8]} Ord: {self.order}{parent_info} Name: {self.name[:30]}>"


class TaskTime(db.Model):
    __tablename__ = "task_time"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.String(36),
        db.ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Link to the user who submitted this review/benchmark
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id = db.Column(
        db.String(36), nullable=False, index=True
    )  # UUID for the recording session or "benchmark"
    task_name = db.Column(
        db.String(255), nullable=False
    )  # Name of the task at time of recording
    time_spent = db.Column(db.Float, nullable=False)  # Time in seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_benchmark = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Relationships
    project = relationship("Project", back_populates="task_times")
    user = relationship("User", back_populates="submitted_reviews")
    gaze_data_points = relationship(
        "GazeData",
        back_populates="task_time_segment",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Optional: Link to the specific Task ID if task_name isn't sufficient
    # task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='SET NULL'), nullable=True, index=True)
    # task = relationship("Task", back_populates="task_time_entries")

    def __repr__(self):
        user_info = f" User: {self.user_id[:8]}" if self.user_id else ""
        return f"<TaskTime ID: {self.id} Sess: {self.session_id[:8]}{user_info} Task: {self.task_name} Bench: {self.is_benchmark}>"


class GazeData(db.Model):
    __tablename__ = "gaze_data"
    # Change BigInteger to Integer for standard auto-increment behavior
    id = db.Column(db.Integer, primary_key=True)
    task_time_id = db.Column(
        db.Integer,
        db.ForeignKey("task_time.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp_ms = db.Column(
        db.BigInteger, nullable=True
    )  # Make timestamp nullable if it might not be sent
    x = db.Column(db.Float, nullable=True)  # Use Float for precision
    y = db.Column(db.Float, nullable=True)

    # Relationships
    task_time_segment = relationship("TaskTime", back_populates="gaze_data_points")

    def __repr__(self):
        # Use safe formatting for potentially None x/y
        pos_str = (
            f"({self.x:.0f}, {self.y:.0f})"
            if self.x is not None and self.y is not None
            else "(None)"
        )
        return f"<GazeData {self.id} TaskTime: {self.task_time_id} Time: {self.timestamp_ms} Pos: {pos_str}>"
