from docker_ops import Docker
from flask import Flask, redirect

app = Flask(__name__)
d = Docker()

@app.route("/")
def hello_word():
    return redirect(code=302)

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