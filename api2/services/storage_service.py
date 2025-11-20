# src/services/storage_service.py
import os
import uuid
import json

import pandas as pd
from flask import current_app
from werkzeug.utils import secure_filename

class StorageService:
    @staticmethod
    def generate_job_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def get_upload_dir(job_id: str) -> str:
        upload_root = current_app.config['UPLOAD_ROOT']
        path = os.path.join(upload_root, job_id)
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def save_file(job_id, file_storage, field_name):
        upload_dir = StorageService.get_upload_dir(job_id)
        sub_dir    = os.path.join(upload_dir, field_name)
        os.makedirs(sub_dir, exist_ok=True)

        # 只取文件名，不要路径前缀
        basename = os.path.basename(file_storage.filename)
        filename = secure_filename(basename)

        target = os.path.join(sub_dir, filename)
        file_storage.save(target)
        return target

    @staticmethod
    def save_config(job_id: str, config: dict) -> str:
        """
        Save the config JSON under:
            <upload_dir>/config/config.json
        """
        upload_dir = StorageService.get_upload_dir(job_id)
        cfg_dir = os.path.join(upload_dir, "config")
        os.makedirs(cfg_dir, exist_ok=True)

        path = os.path.join(cfg_dir, "config.json")
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        return path

    @staticmethod
    def load_config(job_id: str) -> dict:
        """
        Load the config from:
            <upload_dir>/config/config.json
        """
        cfg_path = os.path.join(
            current_app.config['UPLOAD_ROOT'],
            job_id, "config", "config.json"
        )
        with open(cfg_path) as f:
            return json.load(f)

    @staticmethod
    def dataset_path(job_id: str) -> str:
        """
        Locate the uploaded CSV under the job directory.
        We expect it was saved with field_name='dataset_file', so lives in:
            <upload_dir>/dataset_file/<filename>.csv
        """
        upload_dir = StorageService.get_upload_dir(job_id)
        # 先直接定位到 dataset_file 子目录
        candidate_dir = os.path.join(upload_dir, "dataset_file")
        if os.path.isdir(candidate_dir):
            all_files = os.listdir(candidate_dir)
            if all_files:
                return os.path.join(candidate_dir, all_files[0])

        # 如果子目录里没找到，再做一次递归查找（兼容旧版）
        for root, _, files in os.walk(upload_dir):
            for fname in files:
                if fname.lower().endswith(".csv"):
                    return os.path.join(root, fname)

        raise FileNotFoundError(f"No dataset CSV found for job_id={job_id}")

    @staticmethod
    def find_joinpath(job_id):
        upload_dir = StorageService.get_upload_dir(job_id)
        # 先直接定位到 joinpath 子目录
        candidate_dir = os.path.join(upload_dir, "joinpath")
        if os.path.isdir(candidate_dir):
            all_files = os.listdir(candidate_dir)
            if all_files:
                return os.path.join(candidate_dir, all_files[0])

    @staticmethod
    def folder_dir(job_id: str) -> str:
        upload_dir = StorageService.get_upload_dir(job_id)
        return os.path.join(upload_dir, "folder")

    @staticmethod
    def preview_rows(job_id: str, n: int = 50) -> list[dict]:
        """
        Read only the first `n` rows of the stored CSV.
        Returns a list of dicts suitable for JSON.
        """
        path = StorageService.dataset_path(job_id)
        df   = pd.read_csv(path, nrows=n)
        return df.to_dict(orient="records")
