import modal

# Create a Modal app
app = modal.App("agribuddy")

# Define the image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_pyproject("requirements.txt")
    .copy_local_dir("models", "/models")
    .copy_local_dir("static", "/static")
    .copy_local_file("app.py", "/app.py")
    .copy_local_file("utils.py", "/utils.py")
    .copy_local_file("*.csv", "/")
    .copy_local_file("*.xlsx", "/")
)

# Run the Flask app
@app.function(
    image=image,
    allow_concurrent_inputs=100,
    timeout=300,
    memory=2048,  # 2GB RAM
)
@modal.asgi_app()
def flask_app():
    import sys
    sys.path.insert(0, "/")
    from app import app as flask_app
    return flask_app

