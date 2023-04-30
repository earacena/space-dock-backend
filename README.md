
# Space Dock - Backend

## Description

The backend API of a docker container deployment application written in Python with Flask.

The frontend of this project is found [here](https://github.com/earacena/space-dock-frontend).

### Technologies

* Python3
* Flask
* Docker SDK for Python
* Docker

## Usage

### Download

While in terminal with chosen directory, enter the command:

```bash
git clone https://github.com/earacena/space-dock-backend.git
```

### Install

While in the root project folder, create a virtual environment for Python and activate it:

```bash
python3 -m venv venv
source /venv/bin/activate
```

Then using the latest version of pip install the dependencies:

```bash
pip install -r requirements.txt
```

### Deploy locally for development

Ensure that docker or the docker service is running in the background and launch the flask development server:

```bash
flask --app app run
```
