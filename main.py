import docker
import os
import subprocess
import string
import argparse
from io import TextIOWrapper
from docker.models.containers import Container
from docker.models.images import Image

package_install_commands: dict[str, str] = {
    "code-server": "apt-get install -y curl && curl -fsSL https://code-server.dev/install.sh | sh",
    "npm:install": "npm install"
}

def clone_git_repo(git_repo_link: str) -> str:
    """ Clone git repo and return folder path.
    """ 
    result = subprocess.run(["git", "clone", git_repo_link], capture_output=True)
    print(result.stdout)
    
    return 

class Docker:
    """ Wrapper class for Docker operations
    """

    def __init__(self):
        self.client = docker.from_env()

    def create_dockerfile(self, base_image: str, update_command: str, packages: list[str], git_repo_dir: str, start_command: str):
        """ Generates a dockerfile and returns the created file path.
        """
        print("Generating Dockerfile:")
        print(" * Base image: {}".format(base_image))
        print(" * Packages: {}".format(packages))
        print(" * Git repository directory: {}".format(git_repo_dir))
        print(" * Start commands: {}".format(start_command))
        
        print("Generating...")
        
        with open("{}/Dockerfile".format(git_repo_dir), "w") as file:
            # Base image
            file.write("FROM {}\n".format(base_image))
            
            # Move repository files
            file.write("COPY . {}\n".format(git_repo_dir))
            
            # Set working directory for container
            file.write("WORKDIR {}\n".format(git_repo_dir))
            
            # Update container package manager
            file.write("RUN {}\n\n".format(update_command))

            # Install packages
            for package in packages:
                if package in package_install_commands:
                    file.write("# {}\n".format(package))
                    file.write("RUN {}\n".format(
                        package_install_commands[package]))
                    file.write("\n")
            
            # Start command
            file.write("CMD {}\n".format(start_command))
       
        print("Done generating...")
        
    def build_image(self, dockerfile_path: str, tag: str) -> Image:
        print("Building image...")
        (image, logs) = self.client.images.build(
            path=dockerfile_path,
            tag=tag,
        )

        print(logs)

        print("Done building image.")
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

    d = Docker()
    clone_git_repo(args.repo)
    d.create_dockerfile(
        base_image="node:latest",
        update_command="apt-get update",
        packages=[
            "code-server",
            "npm:install"
        ],
        git_repo_dir="{}/".format(args.repo.split(".")[1].split("/")[-1]),    # Assuming using https git link
        start_command="npm run dev"
    )
    d.build_image("{}/".format(args.repo.split(".")[1].split("/")[-1]), "test-image")
    container = d.launch_container("test-image:latest")

main()