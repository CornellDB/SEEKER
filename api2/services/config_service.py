# services/config_service.py
from metam.config import Config

class ConfigService:
    @staticmethod
    def get_global_options():
        # Available group-query methods
        query_methods = [
            {"key": fn.__name__, "label":  fn.__name__}
            for fn in Config.SHARED_GRP_HELPER_LIST
        ]
        # Available profiling scorers
        profilers = [
            {"key": cls.__name__, "label": cls.__name__}
            for cls in Config.SHARED_PROFILER_LIST
        ]
        quality_scorers = [
            {"key": fn.__name__, "label": fn.__name__}
            for fn in Config.SHARED_QUALITYSCORERLIST
        ]
        return {
            "queryMethods": query_methods,
            "profilers":    profilers,
            "qualityScorers": quality_scorers,
        }
