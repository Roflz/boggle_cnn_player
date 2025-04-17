import os
import torch
from torch.utils.data import WeightedRandomSampler

MISCLASSIFIED_DIR = os.path.join("data", "misclassified")

def get_sample_weights(dataset):
    misclassified_set = set()
    for fname in os.listdir(MISCLASSIFIED_DIR):
        if fname.endswith(".png"):
            misclassified_set.add(fname)

    weights = []
    for path, letter, bonus in dataset.samples:
        fname = os.path.basename(path)
        weight = 3.0 if fname in misclassified_set else 1.0
        weights.append(weight)

    weights_tensor = torch.DoubleTensor(weights)
    sampler = WeightedRandomSampler(weights_tensor, num_samples=len(weights_tensor), replacement=True)
    return sampler
