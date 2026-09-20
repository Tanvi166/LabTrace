from app.analysis.metadata_extractor import MetadataExtractorService

def test_ast_metadata_extraction():
    files = {
        "train.py": b"""
import random
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
torch.cuda.manual_seed_all(42)
torch.use_deterministic_algorithms(True)

device = torch.device('cuda')
lr = 0.001
batch_size = 32
epochs = 10
        """,
        "requirements.txt": b"torch==2.1.0\ntorchvision==0.16.0\nnumpy==1.26.0\n",
        "config.yaml": b"learning_rate: 0.001\nbatch_size: 32\noptimizer: Adam\nseed: 42\n"
    }

    meta = MetadataExtractorService.extract_from_files(files)

    assert "PyTorch" in meta.frameworks
    assert "torch" in meta.imports
    assert len(meta.seeds) >= 3
    assert any(s.library == "torch_cpu" for s in meta.seeds)
    assert any(s.library == "numpy" for s in meta.seeds)
    assert meta.dependencies.get("torch") == "2.1.0"
    assert meta.hyperparameters.learning_rate == 0.001
    assert meta.hyperparameters.batch_size == 32
    assert meta.hyperparameters.optimizer == "Adam"
