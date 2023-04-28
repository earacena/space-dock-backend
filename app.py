import docker_ops
import uuid
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": { "origins": "http://localhost:5173" }})
d = docker_ops.Docker()

@app.route("/create/image", methods=['POST'])
def create_image() -> dict[str, str]:
  """ Creates an image.
  """
  # Read git repository link and environment info from body of POST request
  data = request.json
  git_repo_link = data['gitRepositoryLink']
  env_info = data['envInfo']
  
  # Clone repository locally
  repo_id = uuid.uuid4()
  repo_path, repo_name, repo_id = docker_ops.clone_git_repo(git_repo_link, repo_id)
  
  # Create dockerfile using given environment info and essentials
  env_packages = [
    "git",
    "gnupg"
  ]
 
  env_packages += env_info["packages"]
  
  # Generate dockerfile
  d.create_dockerfile(
    base_image=env_info["baseImage"],
    git_repo_dir=repo_path,
    update_command=env_info["updateCommand"],
    packages=env_packages,
    build_command=env_info["buildCommand"],
    start_command=env_info["startCommand"]
  )
  
  # Build image
  image = d.build_image("repos/{}".format(repo_id), repo_name)

  # Remove repo after building
  try:
    shutil.rmtree("repos/{}".format(repo_id))
  except OSError as e:
    print("[Error]: ", e)

  # Send image info as response
  return jsonify({
    "imageId": image.id,
    "imageShortId": image.short_id,
    "repoName": image.tags[0],
    "imageTags": image.tags
  })

@app.route("/create/container/<image_short_id>", methods=["POST"])
def create_container(image_short_id: str):
  """ Creates a container.
  """
  # Launch container
  container = d.launch_container(image_short_id)
  
  # Return response including relevant container information
  return jsonify({
    "containerId": container.id,
    "containerShortId": container.short_id,
    "containerImage": container.attrs['Config']['Image'],
    "containerName": container.name,
    "vscodeUri": d.generate_vscode_connection_uri(container)
  })

@app.route("/fetch/container/logs/<container_short_id>", methods=["GET"])
def fetch_container_logs(container_short_id: str):
  """ Gets a container's logs.
  """
  # Return a generator stream for container logs
  container = d.client.containers.get(container_short_id)
  return container.logs(stream=True)

@app.route("/fetch/image/logs/<image_short_id>", methods=["GET"])
def fetch_image_logs(image_short_id: str):
  """ Gets image build logs.
  """
  image = d.client.images.get(image_short_id)

  logs = []
  for log in d.image_build_logs[image.short_id]:
    # Remove extra newlines
    if "stream" in log and log["stream"] != "\n":
      logs.append(log['stream'].strip("\n"))

  return jsonify({
    "logs": logs
  })


@app.route("/fetch/container/info/all", methods=["GET"])
def fetch_containers():
  """ Gets list containing info for all containers started by space-dock.
  """
  return jsonify({
    "containers": d.get_containers_info(),
  })

@app.route("/fetch/container/info/<container_id>", methods=["GET"])
def fetch_container_info(container_id: str):
  """ Gets info for a container with an id of 'container_id'
  """
  container = d.client.containers.get(container_id)
  
  # Return relevant container info
  return jsonify({
    "containerId": container.id,
    "containerShortId": container.short_id,
    "containerName": container.name,
    "vscodeUri": d.generate_vscode_connection_uri(container)
  })

@app.route("/fetch/image/info/all", methods=["GET"])
def fetch_all_images_info():
  """ Gets list containing info for all images started by space-dock.
  """
  return jsonify({
    "images": d.get_images_info(),
  })

if __name__ == "__main__":
  app.run()
