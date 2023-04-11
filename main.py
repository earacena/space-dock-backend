import docker
import os
import subprocess
import string
import argparse
import uuid
from io import StringIO
from io import TextIOWrapper
from docker.models.containers import Container
from docker.models.images import Image

package_install_commands: dict[str, str] = {
    "code-server": "apt-get install -y curl && curl -fsSL https://code-server.dev/install.sh | sh",
    "npm:install": "npm install",
    "npm:ci": "npm ci",
}

def clone_git_repo(git_repo_link: str, repo_name: str) -> str:
    """ Clone git repo and return folder path.
    """ 
    folder_path = "repos/{}".format(repo_name)
    result = subprocess.run(["git", "clone", git_repo_link, folder_path], capture_output=True, encoding="utf-8")
    
    output = result.stdout
    output_list = output.split('\n')
    
    for line in output_list:
      print(line)
    
    return folder_path

class Docker:
    """ Wrapper class for Docker operations
    """
    def __init__(self):
        self.client = docker.from_env()

    def create_dockerfile(self, base_image: str, update_command: str, packages: list[str], git_repo_dir: str, start_command: str) -> str:
        """ Generates a dockerfile and returns the created file path.
        """
        print("Generating Dockerfile:")
        print(" * Git repository directory: {}".format(git_repo_dir))
        
        with open("{}/Dockerfile".format(git_repo_dir), "w") as file:
          # Base image
          print(" * Base image: {}".format(base_image))
          file.write("FROM {}\n".format(base_image))
        
          # Set working directory for container
          file.write("WORKDIR /usr/src/app\n")
        
          # Move repository files
          file.write("COPY . .\n")
        
          # Update container package manager
          file.write("RUN {}\n\n".format(update_command))

          # Install packages
          print(" * Packages: {}".format(packages))
          for package in packages:
              if package in package_install_commands:
                  file.write("# {}\n".format(package))
                  file.write("RUN {}\n".format(
                      package_install_commands[package]))
        
          file.write("\n")

          # Start command
          print(" * Start command: {}".format(start_command))
          file.write("CMD {}\n".format(start_command))

        print("Done.\n")

        return "{}/Dockerfile".format(git_repo_dir)
        
    def build_image(self, dockerfile_path: str, tag: str) -> Image:
        print("Building image...")
        os.makedirs('dockerfiles/', exist_ok=True)
        
        (image, logs) = self.client.images.build(
            path=dockerfile_path,
            tag=tag,
        )

        print("".join(log['stream'] for log in logs if 'stream' in log))

        print("Done.\n")
        return image

    def launch_container(self, image: str, commands: list[str] = None) -> Container:
        print("Lauching container with image '{}'...".format(image))
        container = self.client.containers.run(image, detach=True)

        print(container.logs())

        # for command in commands:
        #   (_, output) = container.exec_run(command)
        #   print(output)

    def list_active_containers(self) -> list[str]:
        container_ids: list[str] = []
        for container in self.client.containers.list():
            container_ids.append(container.id)

        return container_ids


def main():
    parser = argparse.ArgumentParser(
        prog='space-dock',
        description='A Python application that spins up and manages docker containers.'
    )
    parser.add_argument('repo')

    args = parser.parse_args()

    repo_name = uuid.uuid4()

    d = Docker()
    repo_path = clone_git_repo(args.repo, repo_name)
    d.create_dockerfile(
        base_image="node:latest",
        update_command="apt-get update",
        packages=[
            "code-server",
            "npm:ci",
            "npm:build"
        ],
        git_repo_dir=repo_path,
        start_command="npm start"
    )
    image = d.build_image("repos/{}".format(repo_name), repo_name)
    container = d.launch_container(image.short_id)
    
main()