import docker_ops
import uuid
from flask import Flask, request


app = Flask(__name__)
d = docker_ops.Docker()

@app.route("/create-image", methods=['POST'])
def create_image() -> dict[str, str]:
  # Read git repository link and environment info from body of POST request
  data = request.json
  git_repo_link = data['git_repo_link']
  env_info = data['env_info']
  data = request.json
  git_repo_link = data['git_repo_link']
  env_info = data['env_info']
  
  # Clone repository locally
  repo_id = uuid.uuid4()
  repo_path = docker_ops.clone_git_repo(git_repo_link, repo_id)
  
  # Create dockerfile using given environment info
  env_packages = [
    env_info["build_command"],
    "git",
    "gnupg"
  ]
 
  env_packages += env_info["packages"]
  
  d.create_dockerfile(
    base_image=env_info["base_image"],
    update_command=env_info["update_command"],
    update_command=env_info["update_command"],
    packages=env_packages,
    git_repo_dir=repo_path,
    start_command=env_info["start_command"]
  )
  
  # Build image
  image = d.build_image("repos/{}".format(repo_id), repo_id)
  
  # Send image info as response
  return {
    "image_id": image.id,
    "image_short_id": image.short_id,
    "repo_id": repo_id,
    "base_image": env_info["base_image"],
    "packages": env_packages,
  }

@app.route("/create-container/<image_short_id>", methods=["POST"])
def create_container(image_short_id: str):
  # Launch container
  container = d.launch_container(image_short_id)
  
  # Return response including relevant container information
  return {
    "container_id": container.id,
    "contaienr_short_id": container.short_id,
    "container_name": container.name,
  }

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