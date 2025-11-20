from pathlib import Path

from src.backend.models.BaseModel import BaseModel
from src.backend.models.simpleregression import SimpleRegression
from src.backend.models.simpleclassification import ClassificationModel
from src.backend.profiles.chi2_profile import Chi2Profile
from src.backend.profiles.corr_profile import CorrProfile
from src.backend.profiles.coverage_profile import CoverageProfile
from src.backend.profiles.mutual_profile import MutualInfoProfile
from src.backend.profiles.semantic_profile import SemanticProfile
from src.backend.profiles.syntactics_profile import SyntacticProfile
from src.backend.profiles.uninform_profile import UninformativeProfile
from src.backend.qualityscore.GainProp import ClusterBalanceScorer
from src.backend.qualityscore.ProfileWeighting import ProfileWeightScorer
from src.backend.group_querying.group_helper import (
    identify_group_query_thompson,
    identify_group_query,
)


class Config:
    def __init__(self):
        # Input paths and filenames (edit here directly)
        self.DATA_PATH = None      # Directory for input data files
        self.QUERY_DATA = None     # Main CSV filename
        self.QUERY_PATH = None
        self.JOIN_PATH_FILE = None  # CSV listing join paths

        # Output configuration (edit here directly)
        root = Path(__file__).resolve().parents[1]
        out_dir = root / "output"
        out_dir.mkdir(exist_ok=True)
        self.OUTPUT_PATH = str(out_dir)     # Directory for output files
        self.OUTPUT_FILE = str(out_dir / "augmented_data.csv")  # Output CSV filename

        # Metam algorithm parameters (edit as needed)
        self.UNINFO = 0                  # Number of uninformative profiles to add
        self.EPSILON = 0.05              # Clustering radius parameter
        self.THETA = 100                 # Required utility threshold
        self.CLUSTERS = 5                # Number of clusters
        self.PRED_COL = 'sales'
        self.K = 5
        self.STOPPING_CRITERIA = 100
        self.GRP_SIZE = 1

        self.QUALITYSCORERLIST = [ClusterBalanceScorer, ProfileWeightScorer]
        self.QUALITYSCORER = ClusterBalanceScorer

        self.SCORER_KWARGS = {"decay": 0.8}
        self.GRP_HELPER_LIST = [identify_group_query_thompson, identify_group_query]
        self.GRP_QUERY = identify_group_query_thompson

        self.PROFILER_LIST = [
            CorrProfile,
            MutualInfoProfile,
            SyntacticProfile,
            Chi2Profile,
            SemanticProfile,
            CoverageProfile,
            UninformativeProfile,
        ]
        self.UTILITY_METRIC = None
        self.MODEL = None
        # Miscellaneous
        self.MODEL_MAP: dict[str, type[BaseModel]] = {
            "classification": ClassificationModel,
            "regression": SimpleRegression,
        }

    RANDOM_SEED = 8  # Seed for reproducibility

    SHARED_PROFILER_LIST = [
        CorrProfile,
        MutualInfoProfile,
        SyntacticProfile,
        Chi2Profile,
        SemanticProfile,
        CoverageProfile,
        UninformativeProfile,
    ]
    SHARED_GRP_HELPER_LIST = [identify_group_query_thompson, identify_group_query]
    SHARED_QUALITYSCORERLIST = [ClusterBalanceScorer, ProfileWeightScorer]

    def profiler_factory(self, column_name: str, uninformative: int):
        """
        Instantiate whatever’s in PROFILER_LIST,
        wiring through the args each class needs.
        """
        profs = []
        for cls in self.PROFILER_LIST:
            if cls in (SyntacticProfile, SemanticProfile):
                profs.append(cls(column_name))
            elif cls is UninformativeProfile:
                profs.append(cls(uninformative))
            else:
                profs.append(cls())
        return profs

    def get_model_for_task(self, task: str):
        """
        Instantiate the appropriate BaseModel subclass for this task.
        Raises ValueError if the task isn’t registered.
        """
        model = self.MODEL_MAP.get(task)
        if model is None:
            raise ValueError(f"Unknown task '{task}'.  Supported: {list(self.MODEL_MAP)}")
        return model(self.UTILITY_METRIC)
