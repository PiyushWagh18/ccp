"""
Unit tests for the CloudTask Manager application.
Tests Flask routes, application factory, and service initialisation.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from app import create_app


@pytest.fixture
def app():
    """Create a Flask application instance for testing."""
    # Set test environment variables
    os.environ["AWS_REGION"] = "eu-north-1"
    os.environ["DYNAMODB_TABLE"] = "CloudTasks"
    os.environ["S3_BUCKET"] = "test-bucket"
    os.environ["LAMBDA_FUNCTION_NAME"] = "cloud-task-processor"
    os.environ["CLOUDWATCH_LOG_GROUP"] = "/cloudtask/application"

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


def test_app_creation(app):
    """Test that the Flask application is created successfully."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_app_has_secret_key(app):
    """Test that the application has a SECRET_KEY configured."""
    assert app.config["SECRET_KEY"] is not None
    assert len(app.config["SECRET_KEY"]) > 0


def test_app_config_from_env(app):
    """Test that application configuration is loaded from environment variables."""
    assert app.config["AWS_REGION"] == "eu-north-1"
    assert app.config["DYNAMODB_TABLE"] == "CloudTasks"


def test_health_endpoint(client):
    """Test the health check endpoint returns 200 with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@patch("app.routes.task_routes._get_services")
def test_index_page_loads(mock_services, client):
    """Test that the index page loads successfully with mocked services."""
    # Mock all service methods
    mock_monitoring = MagicMock()
    mock_db = MagicMock()
    mock_db.get_all_tasks.return_value = []
    mock_services.return_value = {
        "db": mock_db,
        "storage": MagicMock(),
        "notifications": MagicMock(),
        "processor": MagicMock(),
        "monitoring": mock_monitoring,
    }

    response = client.get("/")
    assert response.status_code == 200
    assert b"CloudTask Manager" in response.data


@patch("app.routes.task_routes._get_services")
def test_create_task_page_loads(mock_services, client):
    """Test that the task creation form page loads."""
    response = client.get("/tasks/create")
    assert response.status_code == 200
    assert b"Create New Task" in response.data


@patch("app.routes.task_routes._get_services")
def test_create_task_requires_title(mock_services, client):
    """Test that creating a task without a title redirects with an error."""
    mock_services.return_value = {
        "db": MagicMock(),
        "storage": MagicMock(),
        "notifications": MagicMock(),
        "processor": MagicMock(),
        "monitoring": MagicMock(),
    }

    response = client.post("/tasks", data={"title": "", "description": "Test"})
    # Should redirect back to the form
    assert response.status_code == 302


@patch("app.routes.task_routes._get_services")
def test_create_task_success(mock_services, client):
    """Test successful task creation with valid data."""
    mock_db = MagicMock()
    mock_db.create_task.return_value = {"success": True}
    mock_processor = MagicMock()
    mock_processor.process_task.return_value = {"success": True}
    mock_notifications = MagicMock()
    mock_monitoring = MagicMock()

    mock_services.return_value = {
        "db": mock_db,
        "storage": MagicMock(),
        "notifications": mock_notifications,
        "processor": mock_processor,
        "monitoring": mock_monitoring,
    }

    response = client.post(
        "/tasks",
        data={
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending",
            "priority": "medium",
        },
    )
    # Should redirect to index
    assert response.status_code == 302
    # Verify DynamoDB was called
    mock_db.create_task.assert_called_once()


@patch("app.routes.task_routes._get_services")
def test_view_nonexistent_task(mock_services, client):
    """Test viewing a task that does not exist redirects with an error."""
    mock_db = MagicMock()
    mock_db.get_task.return_value = None
    mock_services.return_value = {
        "db": mock_db,
        "storage": MagicMock(),
        "notifications": MagicMock(),
        "processor": MagicMock(),
        "monitoring": MagicMock(),
    }

    response = client.get("/tasks/nonexistent-id")
    assert response.status_code == 302


@patch("app.routes.task_routes._get_services")
def test_delete_task_success(mock_services, client):
    """Test successful task deletion."""
    mock_db = MagicMock()
    mock_db.get_task.return_value = {"task_id": "test-id", "title": "Test", "attachment_key": ""}
    mock_db.delete_task.return_value = {"success": True}
    mock_notifications = MagicMock()
    mock_monitoring = MagicMock()

    mock_services.return_value = {
        "db": mock_db,
        "storage": MagicMock(),
        "notifications": mock_notifications,
        "processor": MagicMock(),
        "monitoring": mock_monitoring,
    }

    response = client.post("/tasks/test-id/delete")
    assert response.status_code == 302
    mock_db.delete_task.assert_called_once_with("test-id")


def test_cloudlib_import():
    """Test that the custom cloudlib library can be imported."""
    from cloudlib import CloudManager, CloudStorageManager, CloudDatabaseManager
    from cloudlib import CloudNotificationManager, CloudLogger, CloudComputeManager

    assert CloudManager is not None
    assert CloudStorageManager is not None
    assert CloudDatabaseManager is not None
    assert CloudNotificationManager is not None
    assert CloudLogger is not None
    assert CloudComputeManager is not None


def test_cloudlib_version():
    """Test that cloudlib reports the correct version."""
    import cloudlib
    assert cloudlib.__version__ == "1.0.0"
