"""
Task routes for the CloudTask Manager application.
Implements full CRUD operations for task management with
integration of five AWS cloud services: DynamoDB, S3, SNS, Lambda, CloudWatch.
"""
import io
import uuid
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
)
from app.services.dynamodb_service import TaskDatabaseService
from app.services.s3_service import TaskStorageService
from app.services.sns_service import TaskNotificationService
from app.services.lambda_service import TaskProcessorService
from app.services.cloudwatch_service import AppMonitoringService

# Create the tasks blueprint for modular route registration
task_bp = Blueprint("tasks", __name__)


def _get_services():
    """
    Initialize and return all cloud service instances.

    Returns:
        dict: Dictionary containing all service instances used by the application.
    """
    return {
        "db": TaskDatabaseService(),
        "storage": TaskStorageService(),
        "notifications": TaskNotificationService(),
        "processor": TaskProcessorService(),
        "monitoring": AppMonitoringService(),
    }


@task_bp.route("/")
def index():
    """
    Display all tasks - READ operation.
    Retrieves all tasks from DynamoDB and renders the task list page.
    Logs page access to CloudWatch.
    """
    services = _get_services()
    services["monitoring"].log_event("Page accessed: Task List")
    tasks = services["db"].get_all_tasks()
    # Sort tasks by creation date, newest first
    tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return render_template("index.html", tasks=tasks)


@task_bp.route("/tasks/create", methods=["GET"])
def create_task_form():
    """Display the task creation form."""
    return render_template("create_task.html")


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    """
    Create a new task - CREATE operation.
    Processes form data, uploads attachment to S3, saves task to DynamoDB,
    invokes Lambda for background processing, sends SNS notification,
    and logs the event to CloudWatch.
    """
    services = _get_services()

    # Generate unique task ID and timestamps
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Collect and sanitise form data
    task_data = {
        "task_id": task_id,
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "status": request.form.get("status", "pending"),
        "priority": request.form.get("priority", "medium"),
        "created_at": now,
        "updated_at": now,
        "attachment_key": "",
        "attachment_name": "",
    }

    # Validate required fields
    if not task_data["title"]:
        flash("Task title is required.", "error")
        return redirect(url_for("tasks.create_task_form"))

    # Handle file attachment upload to S3
    file = request.files.get("attachment")
    if file and file.filename:
        upload_result = services["storage"].upload_attachment(file, file.filename)
        if upload_result["success"]:
            task_data["attachment_key"] = upload_result["key"]
            task_data["attachment_name"] = file.filename

    # Save task to DynamoDB
    result = services["db"].create_task(task_data)

    if result["success"]:
        # Invoke Lambda function for background processing
        services["processor"].process_task(task_data)

        # Send SNS notification about the new task
        services["notifications"].notify_task_created(task_data)

        # Log creation event to CloudWatch
        services["monitoring"].log_event(f"Task created: {task_data['title']}")
        services["monitoring"].record_task_metric("TasksCreated")

        flash("Task created successfully!", "success")
    else:
        flash("Failed to create task. Please try again.", "error")

    return redirect(url_for("tasks.index"))


@task_bp.route("/tasks/<task_id>")
def view_task(task_id):
    """
    View a single task - READ operation.
    Retrieves task from DynamoDB and generates presigned S3 URL for attachment.
    """
    services = _get_services()
    services["monitoring"].log_event(f"Task viewed: {task_id}")

    task = services["db"].get_task(task_id)
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("tasks.index"))

    # Generate a temporary presigned URL for the attachment if one exists
    attachment_url = None
    if task.get("attachment_key"):
        attachment_url = services["storage"].get_attachment_url(task["attachment_key"])

    return render_template("view_task.html", task=task, attachment_url=attachment_url)


@task_bp.route("/tasks/<task_id>/edit", methods=["GET"])
def edit_task_form(task_id):
    """Display the task edit form pre-populated with existing data."""
    services = _get_services()
    task = services["db"].get_task(task_id)
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("tasks.index"))
    return render_template("edit_task.html", task=task)


@task_bp.route("/tasks/<task_id>/update", methods=["POST"])
def update_task(task_id):
    """
    Update an existing task - UPDATE operation.
    Updates task attributes in DynamoDB, handles attachment replacement in S3,
    sends notification via SNS, and logs to CloudWatch.
    """
    services = _get_services()

    # Verify the task exists before updating
    existing_task = services["db"].get_task(task_id)
    if not existing_task:
        flash("Task not found.", "error")
        return redirect(url_for("tasks.index"))

    # Collect updated form data
    updated_data = {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "status": request.form.get("status", existing_task.get("status", "pending")),
        "priority": request.form.get("priority", existing_task.get("priority", "medium")),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Validate required fields
    if not updated_data["title"]:
        flash("Task title is required.", "error")
        return redirect(url_for("tasks.edit_task_form", task_id=task_id))

    # Handle file attachment replacement in S3
    file = request.files.get("attachment")
    if file and file.filename:
        # Delete old attachment from S3 if it exists
        if existing_task.get("attachment_key"):
            services["storage"].delete_attachment(existing_task["attachment_key"])
        # Upload new attachment to S3
        upload_result = services["storage"].upload_attachment(file, file.filename)
        if upload_result["success"]:
            updated_data["attachment_key"] = upload_result["key"]
            updated_data["attachment_name"] = file.filename

    # Update the task in DynamoDB
    result = services["db"].update_task(task_id, updated_data)

    if result["success"]:
        # Send update notification via SNS
        services["notifications"].notify_task_updated(task_id, updated_data["title"])
        # Log the update event to CloudWatch
        services["monitoring"].log_event(f"Task updated: {updated_data['title']}")
        services["monitoring"].record_task_metric("TasksUpdated")
        flash("Task updated successfully!", "success")
    else:
        flash("Failed to update task. Please try again.", "error")

    return redirect(url_for("tasks.view_task", task_id=task_id))


@task_bp.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id):
    """
    Delete a task - DELETE operation.
    Removes the task from DynamoDB, deletes attachment from S3,
    sends deletion notification via SNS, and logs to CloudWatch.
    """
    services = _get_services()

    # Retrieve task to find its attachment key before deletion
    task = services["db"].get_task(task_id)
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("tasks.index"))

    # Delete attachment from S3 if it exists
    if task.get("attachment_key"):
        services["storage"].delete_attachment(task["attachment_key"])

    # Delete the task record from DynamoDB
    result = services["db"].delete_task(task_id)

    if result["success"]:
        # Send deletion notification via SNS
        services["notifications"].notify_task_deleted(task.get("title", "Unknown"))
        # Log the deletion to CloudWatch
        services["monitoring"].log_event(f"Task deleted: {task.get('title', 'Unknown')}")
        services["monitoring"].record_task_metric("TasksDeleted")
        flash("Task deleted successfully!", "success")
    else:
        flash("Failed to delete task. Please try again.", "error")

    return redirect(url_for("tasks.index"))


@task_bp.route("/tasks/<task_id>/download")
def download_attachment(task_id):
    """
    Download a task's file attachment from S3.
    Retrieves the file from S3 and streams it to the user's browser.
    """
    services = _get_services()
    task = services["db"].get_task(task_id)

    if not task or not task.get("attachment_key"):
        flash("No attachment found.", "error")
        return redirect(url_for("tasks.view_task", task_id=task_id))

    # Download the file content from S3
    result = services["storage"].download_attachment(task["attachment_key"])
    if result["success"]:
        return send_file(
            io.BytesIO(result["body"].read()),
            download_name=task.get("attachment_name", "attachment"),
            as_attachment=True,
        )

    flash("Failed to download attachment.", "error")
    return redirect(url_for("tasks.view_task", task_id=task_id))


@task_bp.route("/health")
def health_check():
    """
    Health check endpoint for application monitoring.
    Returns JSON status indicating the application is running.
    """
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
