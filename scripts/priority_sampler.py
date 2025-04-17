import os
import torch
from torch.utils.data import WeightedRandomSampler

MISCLASSIFIED_DIR = os.path.join("data", "misclassified")

def get_sample_weights(dataset):
    from collections import Counter
    import numpy as np

    if hasattr(dataset, 'samples'):
        samples = dataset.samples
    elif hasattr(dataset, 'dataset') and hasattr(dataset, 'indices'):
        # It's a Subset
        samples = [dataset.dataset.samples[i] for i in dataset.indices]
    else:
        raise ValueError("Unsupported dataset type passed to get_sample_weights")

    letter_counts = Counter(letter for _, letter, _ in samples)
    weights = []

    for _, letter, _ in samples:
        freq = letter_counts[letter]
        weights.append(1.0 / freq if freq > 0 else 1.0)

    return torch.utils.data.WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
