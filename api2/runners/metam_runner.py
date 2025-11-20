# api2/runners/metam_runner.py

import os
import sys
import traceback

from metam.config import Config
from metam import pipeline
import queue

# locate the same uploads folder you configured in app.py
API2_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_ROOT = os.path.join(API2_DIR, 'uploads')

class VariantQueue:
    """
    A tiny wrapper around the central queue that tags
    every message with self.variant before putting.
    """
    def __init__(self, central_q: queue.Queue, variant: int):
        self._q  = central_q
        self._vid = variant

    def put(self, msg: dict):
        msg['variant'] = self._vid
        self._q.put(msg)

def run_metam_for_job(
    job_id: str,
    variant_id: int,
    cfg: dict,
    central_q: queue.Queue
):
    """
    1) Find CSV / joinpath / folder under uploads/<job_id>/
    2) Override Config.* so the shared pipeline loads correctly
    3) Wrap central_q so every msg gets tagged with `variant_id`
    4) Execute the METAM pipeline with the tagged queue
    """
    local_config = Config()
    # 1) paths
    upload_dir = os.path.join(UPLOAD_ROOT, job_id)

    # main CSV
    csv_dir = os.path.join(upload_dir, 'dataset_file')
    csv_path = next(
        os.path.join(csv_dir, f)
        for f in os.listdir(csv_dir)
        if f.lower().endswith('.csv')
    )
    local_config.QUERY_PATH = csv_path
    local_config.QUERY_DATA = os.path.basename(csv_path)

    # optional joinpath
    jp_dir = os.path.join(upload_dir, 'joinpath')
    if os.path.isdir(jp_dir) and os.listdir(jp_dir):
        local_config.JOIN_PATH_FILE = os.path.join(jp_dir, os.listdir(jp_dir)[0])

    # optional folder of aux files
    folder_dir = os.path.join(upload_dir, 'folder')
    if os.path.isdir(folder_dir) and os.listdir(folder_dir):
        local_config.DATA_PATH = folder_dir

    # 2) override this variant’s algorithmic settings
    local_config.UTILITY_METRIC = cfg.get('metric')

    local_config.MODEL           = local_config.get_model_for_task(cfg.get('task'))
    local_config.PRED_COL       = cfg.get('attribute')

    # let the front-end tell us which profilers to use
    selected = cfg.get('profilers')  # e.g. ["CorrProfile","CoverageProfile"]
    if selected is not None:
        name2cls = {cls.__name__: cls for cls in Config.SHARED_PROFILER_LIST}
        # filter & reassign the global list
        local_config.PROFILER_LIST = [name2cls[name] for name in selected if name in name2cls]
    # group‐query helper (if you need it)

    gm = cfg.get('queryMethod')
    for fn in Config.SHARED_GRP_HELPER_LIST:
        if fn.__name__ == gm:
            local_config.GRP_QUERY = fn
            break

    Sco = cfg.get('qualityScorers')
    for fn in Config.SHARED_QUALITYSCORERLIST:
        if fn.__name__ == Sco:
            local_config.QUALITYSCORER = fn
            break



    # 3) wrap the central queue so that every msg gets variant_id
    tagged_q = VariantQueue(central_q, variant_id)

    # 4) run METAM
    try:
        pipeline.main(event_queue=tagged_q, local_config=local_config)
    except Exception as e:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        tagged_q.put({"type": "error", "message": str(e)})
