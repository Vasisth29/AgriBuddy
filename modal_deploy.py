import modal

# Create a Modal app
app = modal.App("agribuddy")

# Define the image with all dependencies and local files
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir("models", remote_path="/models")
    .add_local_dir("static", remote_path="/static")
    .add_local_file("app.py", remote_path="/app.py")
    .add_local_dir("templates", remote_path="/templates") 
    .add_local_file("utils.py", remote_path="/utils.py")
    .add_local_file("Sub_Division_IMD_2017.csv", remote_path="/Sub_Division_IMD_2017.csv")
    .add_local_file("crop_production.csv", remote_path="/crop_production.csv")
    .add_local_file("Crop_recommendation.csv", remote_path="/Crop_recommendation.csv")
    .add_local_file("merged_crop_data.csv", remote_path="/merged_crop_data.csv")
    .add_local_file("soil_nutrient_data.xlsx", remote_path="/soil_nutrient_data.xlsx")
    .add_local_file("state_climate.csv", remote_path="/state_climate.csv")
)

# Run the Flask app
@app.function(
    image=image,
    allow_concurrent_inputs=100,
    timeout=300,
    memory=2048,  # 2GB RAM on Modal free tier
)
@modal.wsgi_app()  # Flask is WSGI
def flask_app():
    import sys
    sys.path.insert(0, "/")
    from app import app as flask_app
    return flask_app