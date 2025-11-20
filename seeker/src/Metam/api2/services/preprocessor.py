# src/services/preprocessor.py

import pandas as pd
from .storage_service import StorageService

def preprocess_file(job_id: str, n_preview: int = 50) -> list[dict]:
    """
    1) 读取上传到 disk 的 CSV
    2) 丢弃任何有 NaN 的行
    3) 覆盖保存原文件
    4) 返回前 n_preview 条记录，用于前端预览
    """
    # 找到存储路径
    path = StorageService.dataset_path(job_id)

    # 读取、简单清洗
    df = pd.read_csv(path)
    df_clean = df.dropna()

    # 覆盖写回
    df_clean.to_csv(path, index=False)

    # 返回前 n_preview 行
    return df_clean.head(n_preview).to_dict(orient="records")
