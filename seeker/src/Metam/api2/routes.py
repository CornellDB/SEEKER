# api2/routes.py
import os
from flask import request, jsonify
from flask_restful import Resource
import uuid
import json
from flask import request, current_app
from flask_restful import Resource
from werkzeug.utils import secure_filename

from api2.services.config_service import ConfigService
from services.preprocessor import preprocess_file
from services.utility_service import calculate_utility
from services.storage_service import StorageService
from services.result_service  import ResultsService
from utils.sse                 import sse_stream

class PrepareResource(Resource):
    def post(self):
        data  = request.get_json(force=True)
        job_id = data.get("job_id")
        if not job_id:
            return {"message":"job_id required"}, 400
        preview = preprocess_file(job_id)
        return {"job_id": job_id, "preview": preview}, 200

class UtilityResource(Resource):
    def post(self):
        data      = request.get_json(force=True)
        job_id    = data.get("job_id")
        task      = data.get("task")
        attribute = data.get("attribute")
        metric    = data.get("utilityMetric")

        # basic validation
        if not all([job_id, task, attribute, metric]):
            return {"message": "job_id, task, attribute and utilityMetric required"}, 400

        try:
            score = calculate_utility(job_id, task, attribute, metric)
            return jsonify({"score": score})
        except Exception as e:
            current_app.logger.exception(e)
            return {"message": str(e)}, 500

class FileResource(Resource):
    def post(self):
        """Initial upload: returns new job_id and saved path."""
        file_obj = request.files.get('dataset_file')
        if not file_obj:
            return {"message": "No file provided."}, 400

        job_id = StorageService.generate_job_id()
        saved_path = StorageService.save_file(job_id, file_obj, 'dataset_file')
        return {"job_id": job_id, "file_path": saved_path}, 201

    def put(self):
        """Replace an existing file under known job_id."""
        job_id = request.form.get('job_id')
        file_obj = request.files.get('dataset_file')
        if not job_id or not file_obj:
            return {"message": "Both job_id and file must be provided."}, 400

        saved_path = StorageService.save_file(job_id, file_obj, 'dataset_file')
        return {"job_id": job_id, "file_path": saved_path}, 200


class ConfigResource(Resource):
    def post(self):
        """Initial config write for a new or existing job."""
        data = request.get_json(force=True)
        job_id = data.get('job_id')
        settings = data.get('settings')
        if not job_id or settings is None:
            return {"message": "job_id and settings JSON required"}, 400

        config_path = StorageService.save_config(job_id, settings)
        return {"job_id": job_id, "config_path": config_path}, 201

    def put(self):
        """Replace config for an existing job."""
        data = request.get_json(force=True)
        job_id = data.get('job_id')
        settings = data.get('settings')
        if not job_id or settings is None:
            return {"message": "job_id and settings JSON required"}, 400

        config_path = StorageService.save_config(job_id, settings)
        return {"job_id": job_id, "config_path": config_path}, 200

    def get(self, job_id):
        """Retrieve current config for job_id."""
        try:
            cfg = StorageService.load_config(job_id)
            return {"job_id": job_id, "settings": cfg}, 200
        except FileNotFoundError:
            return {"message": f"No config for job {job_id}"}, 404


class PreviewResource(Resource):
    """
    GET  /api/preview/<job_id>?n=50
    Returns the first `n` rows (default 50) of the uploaded CSV.
    """
    def get(self, job_id: str):
        # parse & validate `n` query param
        try:
            n = int(request.args.get("n", 50))
            if n < 1:
                raise ValueError
        except ValueError:
            return {"message": "`n` must be a positive integer"}, 400

        try:
            rows = StorageService.preview_rows(job_id, n=n)
            return {"job_id": job_id, "preview": rows}, 200
        except FileNotFoundError as fe:
            return {"message": str(fe)}, 404
        except Exception as e:
            current_app.logger.exception(e)
            return {"message": "Failed to generate preview"}, 500


class JoinPathResource(Resource):
    def post(self):
        """
        上传单个“joinable paths”文件到 job_id 目录。
        """
        job_id  = request.form.get("job_id")
        file_obj = request.files.get("joinpath_file")
        if not job_id or not file_obj:
            return {"message": "job_id and joinpath_file required"}, 400

        saved = StorageService.save_file(job_id, file_obj, "joinpath")
        return {"job_id": job_id, "path": saved}, 201

class FolderResource(Resource):
    def post(self):
        """
        上传整个文件夹（多选文件）到 job_id 目录，每个文件前缀 “folder__” 保存。
        """
        job_id = request.form.get("job_id")
        files  = request.files.getlist("folder_files")
        if not job_id or not files:
            return {"message": "job_id and folder_files required"}, 400

        paths = []
        for f in files:
            p = StorageService.save_file(job_id, f, "folder")
            paths.append(p)
        return {"job_id": job_id, "paths": paths}, 201


class MetamStartResource(Resource):
    def post(self):
        """
        接收前端参数后启动 METAM。
        JSON body 中需要：
          - job_id: 已上传 CSV 的 ID
          - joinpathPath (可选): join-path JSON/CSV 在服务器上的完整路径
          - folderPaths (可选): array of strings，已上传的辅助文件列表路径
        """
        data        = request.get_json(force=True)
        job_id      = data.get("job_id")
        variants = data.get("variants")
        if not job_id:
            return {"message":"job_id required"}, 400
        if not variants or not isinstance(variants, list):
            return {"message": "variants array required"}, 400
        ResultsService.start_metam(job_id, variants)
        return {"message":"METAM started"}, 202

class MetamStreamResource(Resource):
    def get(self, job_id):
        """
        Server-Sent Events 端点，用于实时推送：
          - type: 'update' 或 'augmentation'（将来可兼容）
          - type: 'complete' 完成信号
        """
        return sse_stream(ResultsService.stream_events(job_id))

class ConfigOptionsResource(Resource):
    def get(self):
        """Returns global METAM configuration choices."""
        options = ConfigService.get_global_options()
        return options, 200