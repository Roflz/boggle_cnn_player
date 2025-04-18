import os
import torch
import string
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import torch.nn as nn

# === LABEL MAPS (A–Z + 'QU') ===
LETTERS = [chr(i + ord('A')) for i in range(26)] + ['QU']
letter_to_index = {ch: i for i, ch in enumerate(LETTERS)}
index_to_letter = {i: ch for ch, i in letter_to_index.items()}
bonus_to_index = {"normal": 0, "DL": 1, "TL": 2, "DW": 3, "TW": 4}
index_to_bonus = {v: k for k, v in bonus_to_index.items()}

# === CONFIG ===
IMG_SIZE = 28
DATA_DIR = os.path.join("data", "boggle_tiles")
BATCH_SIZE = 64

# === DATASET ===
class TileDataset(Dataset):
    def __init__(self, root_dir=DATA_DIR):
        self.samples = []
        self.transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.Grayscale(),
            transforms.ToTensor()
        ])
        for letter in os.listdir(root_dir):
            letter_dir = os.path.join(root_dir, letter)
            if not os.path.isdir(letter_dir):
                continue
            for fname in os.listdir(letter_dir):
                if fname.endswith(".png") and "__bonus-" in fname:
                    bonus_part = fname.split("__bonus-")[-1].replace(".png", "")
                    self.samples.append((os.path.join(letter_dir, fname), letter, bonus_part))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, letter, bonus = self.samples[idx]
        image = Image.open(path).convert("RGB")
        image = self.transform(image)
        letter_idx = letter_to_index[letter.upper()]
        bonus_idx = bonus_to_index[bonus]
        return image, letter_idx, bonus_idx

# === MODEL ===
class MultiTaskCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
        )
        self.classifier = nn.Linear(64 * 7 * 7, 64)
        self.letter_head = nn.Linear(64, len(letter_to_index))  # 27 output classes
        self.bonus_head = nn.Linear(64, 5)

    def forward(self, x):
        x = self.shared(x)
        x = self.classifier(x)
        return self.letter_head(x), self.bonus_head(x)


from torchvision import transforms
from collections import defaultdict
from PIL import Image
from torch.utils.data import Dataset
import os

# Assuming these are globally defined somewhere
# letter_to_index, bonus_to_index, IMG_SIZE

class AugmentedTileDataset(Dataset):
    def __init__(self, root_dir, augment=True):
        self.samples = []
        self.root_dir = root_dir
        self.augment = augment
        self.augment_transform = transforms.Compose([
            transforms.RandomApply([
                transforms.RandomRotation(15),
                transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
                transforms.ColorJitter(brightness=0.3, contrast=0.3)
            ], p=0.75),
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.Grayscale(),
            transforms.ToTensor()
        ])
        self.standard_transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.Grayscale(),
            transforms.ToTensor()
        ])

        # Gather all samples and count occurrences
        self.class_counts = defaultdict(int)
        for letter in os.listdir(root_dir):
            folder = os.path.join(root_dir, letter)
            if not os.path.isdir(folder):
                continue
            for fname in os.listdir(folder):
                if fname.endswith(".png") and "__bonus-" in fname:
                    bonus = fname.split("__bonus-")[1].replace(".png", "")
                    self.samples.append((os.path.join(folder, fname), letter, bonus))
                    self.class_counts[letter] += 1

        # Rare classes have fewer than 10 samples
        self.rare_classes = {label for label, count in self.class_counts.items() if count < 10}
        print(f"🧬 Augmenting rare classes: {sorted(self.rare_classes)}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, letter, bonus = self.samples[idx]
        image = Image.open(path).convert("RGB")
        if self.augment and letter in self.rare_classes:
            image = self.augment_transform(image)
        else:
            image = self.standard_transform(image)

        letter_idx = letter_to_index[letter.upper()]
        bonus_idx = bonus_to_index[bonus]
        return image, letter_idx, bonus_idx
