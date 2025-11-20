import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from src.backend.profiles.base_profile import BaseProfile

_tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')


def _mean_pooling(outputs, mask):
    token_emb = outputs.last_hidden_state  # (batch, seq, dim)
    mask = mask.unsqueeze(-1).float()
    return (token_emb * mask).sum(1) / mask.sum(1)

class SemanticProfile(BaseProfile):
    def __init__(self, orig_name: str):
        self.orig_name = orig_name
    def name(self) -> str:
        return "semantic"

    def score(self, df, new_col):
        # embed dataset header
        headers = list(df.columns)
        embs = []
        for h in headers:
            toks = _tokenizer(h, return_tensors='pt', truncation=True)
            out = _model(**toks)
            embs.append(_mean_pooling(out, toks['attention_mask']))
        ds_emb = torch.mean(torch.stack(embs), dim=0)

        # embed col's orignial name
        toks2 = _tokenizer(self.orig_name, return_tensors='pt', truncation=True)
        out2 = _model(**toks2)
        new_emb = _mean_pooling(out2, toks2['attention_mask'])

        # cosine sim
        sim = F.cosine_similarity(ds_emb, new_emb, dim=-1).item()
        return {"all": 1.0 - max(min(sim, 1.0), -1.0)}
