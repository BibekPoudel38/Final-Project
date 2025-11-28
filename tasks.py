import os
import sys
from invoke import task

# Define paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend", "BizAI")
PREDICTION_DIR = os.path.join(PROJECT_ROOT, "prediction_model")


@task
def install_invoke(c):
    """Installs invoke and colorama if not already installed."""
    c.run(f"{sys.executable} -m pip install invoke colorama")


@task
def install_all(c):
    """Installs all dependencies for local development (Backend, Prediction, Dev Tools)."""
    print("Installing Root Dependencies...")
    c.run(f"{sys.executable} -m pip install -r requirements.txt")

    print("\nInstalling Backend Dependencies...")
    # Note: The file is named 'requriements.txt' in the backend folder based on directory listing
    if os.path.exists(os.path.join(BACKEND_DIR, "requriements.txt")):
        c.run(f"{sys.executable} -m pip install -r backend/requriements.txt")
    elif os.path.exists(os.path.join(BACKEND_DIR, "requirements.txt")):
        c.run(f"{sys.executable} -m pip install -r backend/requirements.txt")

    print("\nInstalling Prediction Model Dependencies...")
    c.run(f"{sys.executable} -m pip install -r prediction_model/requirements.txt")

    print("\nInstalling Frontend Dependencies...")
    with c.cd(FRONTEND_DIR):
        c.run("npm install")

    print("\nAll dependencies installed.")


@task
def up(c, build=False, detach=True):
    """Starts all services in production mode."""
    cmd = "docker-compose -f docker-compose.yml up"
    if build:
        cmd += " --build"
    if detach:
        cmd += " -d"
    c.run(cmd)


@task
def down(c):
    """Stops all services."""
    c.run("docker-compose -f docker-compose.yml down")


@task
def clean(c):
    """Stops services and removes containers, networks, volumes, and images."""
    print("Cleaning up Docker resources...")
    c.run("docker-compose -f docker-compose.yml down -v --rmi local --remove-orphans")
    print("Cleanup complete.")


@task
def debug(c, build=False):
    """Starts all services in debug mode (exposed ports, interactive)."""
    cmd = "docker-compose -f docker-compose.yml -f docker-compose.debug.yml up"
    if build:
        cmd += " --build"
    c.run(cmd)


@task
def logs(c, service=""):
    """View logs. Usage: inv logs [service_name]"""
    c.run(f"docker-compose logs -f {service}")


@task
def migrate(c):
    """Runs Django migrations inside the container."""
    print("Running Django Migrations...")
    c.run("docker-compose exec backend python manage.py migrate")


@task
def makemigrations(c):
    """Runs Django makemigrations inside the container."""
    c.run("docker-compose exec backend python manage.py makemigrations")


@task
def restart(c, service):
    """Restarts a specific service. Usage: inv restart <service_name>"""
    c.run(f"docker-compose restart {service}")


@task
def pull_model(c, model="llama3"):
    """Pulls an LLM model into the Ollama container. Usage: inv pull-model <model_name>"""
    print(f"Pulling model '{model}' in Ollama container...")
    c.run(f"docker-compose exec ollama ollama pull {model}")


@task
def shell_backend(c):
    """Opens a shell inside the backend container."""
    c.run("docker-compose exec backend /bin/bash")


@task
def shell_frontend(c):
    """Opens a shell inside the frontend container."""
    c.run("docker-compose exec frontend /bin/sh")
