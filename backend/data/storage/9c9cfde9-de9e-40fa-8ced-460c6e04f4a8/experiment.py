import torch
import torchvision
import random
import numpy as np

SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

print("Dataset: CIFAR-10")
print("Model: ResNet18")
print("Epochs: 10")
print("Batch size: 64")
print("Learning rate: 0.001")
print("Optimizer: Adam")
print("Seed: 42")