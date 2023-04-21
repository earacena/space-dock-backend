import os
import subprocess
import string
import argparse
import uuid
import docker
from docker.models.containers import Container
from docker.models.images import Image
from io import StringIO
from io import TextIOWrapper

# Install commands are based on Alpine Linux package manager (apk)
package_install_commands: dict[str, str] = {
    "gnupg": "apk add gnupg",
    "git": "apk add git",
    "npm:install": "npm install",
    "npm:build": "npm run build",
    "npm:ci": "npm ci",
}


def clone_git_repo(git_repo_link: str, repo_name: str) -> str:
    """ Clone git repo and return folder path.
    """
    folder_path = "repos/{}".format(repo_name)

    result = subprocess.run(["git", "clone", git_repo_link,
                            folder_path], capture_output=True, text=True, check=True)
    print("\n{}".format(result.stderr))

    return folder_path


def open_vscode_in_container(repo_id: str) -> None:
    """ Use VsCode commandline option folder-uri to connect to container.
        Note: Requires Dev - Containers extension
    """
    subprocess.run(["code", "--folder-uri",
                   "vscode-remote://attached-container+{}/app".format(repo_id.encode('utf-8').hex())])
    return


class Docker:
    """ Wrapper class for Docker operations
    """

    def __init__(self):
        self.client = docker.from_env()

        # Storage for image build logs
        self.image_build_logs = {}

        # Storage for image info
        self.image_info = {}

    def create_dockerfile(self, base_image: str, update_command: str, packages: list[str], git_repo_dir: str, build_command: str, start_command: str) -> str:
        """ Generates a dockerfile and returns the created file path.
        """
        print("Generating Dockerfile:")
        print(" * Git repository directory: {}".format(git_repo_dir))

        with open("{}/Dockerfile".format(git_repo_dir), "w") as file:
            # Base image
            print(" * Base image: {}".format(base_image))
            file.write("FROM {}\n".format(base_image))

            # Set working directory for container
            file.write("WORKDIR app/\n")

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

            # Run build command
            file.write("RUN {}\n".format(build_command))

            # Start command
            print(" * Start command: {}".format(start_command))
            file.write("CMD {}\n".format(start_command))

        print("Done.\n")

        return "{}/Dockerfile".format(git_repo_dir)

    def build_image(self, dockerfile_path: str, tag: str) -> Image:
        print("Building image...")

        (image, logs) = self.client.images.build(
            path=dockerfile_path,
            tag=tag,
        )

        # Store image build logs
        self.image_build_logs[image.short_id] = logs

        print("Done.\n")
        return image

    def launch_container(self, image: str, commands: list[str] = None) -> Container:
        print("Lauching container with image '{}'...".format(image))
        container = self.client.containers.run(
            image,
            labels={"manager": "space-dock"},
            ports={8080: 8080},
            detach=True
        )

        # for command in commands:
        #   (_, output) = container.exec_run(command)
        #   print(output)

        return container

    def retrieve_container_logs(self, container: Container) -> list[str]:
        """ Gets containers logs and decodes them into a list of strings.
        """
        logs = container.logs()
        decoded: list[str] = []
        for line in logs:
            line = line.decode(encoding="utf-8").strip('\n')
            decoded.append(line)

        return decoded

    def generate_vscode_connection_uri(self, container: Container) -> str:
        """ Creates the URI string needed to connect VsCode to container.
        """
        container_id_hex = container.short_id.encode('utf-8').hex()
        return "vscode://vscode-remote/attached-container+{}/app".format(container_id_hex)

    def get_containers_info(self) -> list[dict[str, str]]:
        """ Retrieve a list containing info of all active containers.
            Each entry in list will include:
              containerId: str
              containerShortId: str
              containerName: str
              containerImage: str
              containerStatus: str
              vscodeUri: str
        """
        containers_info: dict[str, str] = []

        for container in self.client.containers.list(all=True, filters={"label": "manager=space-dock"}):
            containers_info.append({
                "containerId": container.id,
                "containerShortId": container.short_id,
                "containerName": container.name,
                "containerImage": container.attrs['Config']['Image'],
                "containerStatus": container.status,
                "vscodeUri": self.generate_vscode_connection_uri(container)
            })

        return containers_info

    def get_images_info(self) -> dict[str, str]:
        """ Retrieve a list containing info of images.
            Each entry in list will include:
              image_id: str
              image_short_id: str,
              repo_id: str,
              base_image: str,
              packages: list[str],
        """
        return [info for _, info in self.image_info.items()]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='docker_ops',
        description='A Python wrapper for Docker SDK that spins up and manages docker containers.'
    )
    parser.add_argument('git-repository-link')

    args = parser.parse_args()

    repo_name = uuid.uuid4()

    d = Docker()
    repo_path = clone_git_repo(args.repo, repo_name)
    d.create_dockerfile(
        base_image="node:current-alpine",
        git_repo_dir=repo_path,
        update_command="apk update",
        packages=[
            "git",
            "gnupg"
        ],
        build_command="npm ci;npm build",
        start_command="npm run dev"
    )
    image = d.build_image("repos/{}".format(repo_name), repo_name)
    container = d.launch_container(image.short_id)

    for log in d.retrieve_container_logs(container):
        print(log)
