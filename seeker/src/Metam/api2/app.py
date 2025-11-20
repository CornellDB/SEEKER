import os
import random
from metam.config import Config
import numpy as np
from flask import Flask
from flask_restful import Api
from routes import PrepareResource, UtilityResource, ConfigResource, FileResource, PreviewResource, JoinPathResource, \
    FolderResource, MetamStartResource, MetamStreamResource, ConfigOptionsResource
import warnings
warnings.filterwarnings('ignore')

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    upload_folder = os.path.join(basedir, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_ROOT'] = upload_folder
    random.seed(Config.RANDOM_SEED)
    np.random.seed(Config.RANDOM_SEED)

    api = Api(app)
    api.add_resource(PrepareResource, "/api/prepare")
    api.add_resource(UtilityResource, "/api/utility")
    api.add_resource(FileResource,   "/api/upload/file")
    api.add_resource(ConfigResource, "/api/upload/config", "/api/upload/config/<string:job_id>")
    api.add_resource(
      PreviewResource,
      "/api/preview/<string:job_id>"
    )
    api.add_resource(JoinPathResource, "/api/upload/joinpath")
    api.add_resource(FolderResource, "/api/upload/folder")
    api.add_resource(MetamStartResource,     "/api/metam/start")
    api.add_resource(MetamStreamResource,    "/api/metam/stream/<string:job_id>")
    api.add_resource(ConfigOptionsResource, "/api/config/options")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
    app.config["PROPAGATE_EXCEPTIONS"] = True
