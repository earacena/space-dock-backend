import docker_ops
import uuid
from flask import Flask, request


app = Flask(__name__)
d = docker_ops.Docker()

@app.route("/create-image", methods=['POST'])
def create_image() -> dict[str, str]:
  # Read git repository link and environment info from body of POST request
  git_repo_link = request.form['git_repo_link']
  env_info = request.form['env_info']
  
  # Clone repository locally
  repo_id = uuid.uuid4()
  repo_path = docker_ops.clone_git_repo(git_repo_link, repo_id)
  
  # Create image using given environment info
  env_packages = env_info["build_command"] + env_info["packages"] + ["git"] + "gnupg"
  d.create_dockerfile(
    base_image=env_info["base_image"],
    update_command="apk update",
    packages=env_packages,
    git_repo_dir=repo_path,
    start_command=env_info["start_command"]
  )
  
  # Build image
  image = d.build_image("repos/{}".format(repo_id), repo_id)
  
  # Send image id as response
  return {
    "image_id": image.id,
    "image_short_id": image.short_id,
    "repo_id": repo_id,
    "base_image": env_info["base_image"],
    "packages": env_packages,
  }

@app.route("/create-image")
def create_image():
  pass
  
@app.route("/create-container")
def create_container():
  pass

@app.route("/fetch-containers")
def fetch_containers():
  pass

@app.route("/fetch-container-info/<id>")
def fetch_container_info(id: str):
  pass

@app.route("/fetch-image-info/<id>")
def fetch_image_info(id: str):
  pass

if __name__ == "__main__":
  app.run()