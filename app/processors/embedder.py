"""可选向量化：sentence-transformers + BGE-M3（8GB 内存可跑）。

未安装 sentence-transformers 或 EMBEDDING_ENABLED=false 时自动跳过，
管线仍可用 simhash 去重正常运行。
"""
import logging

import numpy as np

from app.config import get_settings

log = logging.getLogger(__name__)
_model = None
_unavailable = False


def get_model():
    global _model, _unavailable
    if _unavailable:
        return None
    s = get_settings()
    if not s.embedding_enabled:
        _unavailable = True
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            log.info("加载 embedding 模型 %s（首次需下载，几分钟）...", s.embedding_model)
            _model = SentenceTransformer(s.embedding_model)
        except Exception as e:  # noqa: BLE001
            log.warning("embedding 不可用（%s），改用纯 simhash 去重", e)
            _unavailable = True
            return None
    return _model


def embed(texts: list[str]) -> list[np.ndarray] | None:
    model = get_model()
    if model is None:
        return None
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [np.asarray(v, dtype=np.float32) for v in vecs]


def embed_one(text: str) -> np.ndarray | None:
    out = embed([text])
    return out[0] if out else None
