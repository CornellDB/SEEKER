# api2/services/results_service.py
import threading
import queue
from api2.runners.metam_runner import run_metam_for_job

# one queue per job
_queues = {}

class ResultsService:
    @staticmethod
    def start_metam(job_id: str, variants: list):
        """
        Create a central queue, then for each variant spawn a thread
        that runs run_metam_for_job(job_id, variant_id, cfg, central_q).
        """
        central_q = queue.Queue()
        _queues[job_id] = central_q

        for vid, cfg in enumerate(variants):
            threading.Thread(
                target=run_metam_for_job,
                args=(job_id, vid, cfg, central_q),
                daemon=True
            ).start()

    @staticmethod
    def stream_events(job_id: str):
        """
        SSE endpoint: yield all messages from the central queue.
        """
        q = _queues.get(job_id)
        if not q:
            yield {"type": "error", "message": "no such job"}
            return

        while True:
            msg = q.get()
            yield msg
            if msg.get("type") in ("complete","error"):
                break
