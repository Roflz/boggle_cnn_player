import os
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from torch.utils.data import DataLoader
from model_definitions import (
    TileDataset, MultiTaskCNN,
    letter_to_index, index_to_letter,
    bonus_to_index, index_to_bonus,
    DATA_DIR, IMG_SIZE, BATCH_SIZE
)
from collections import defaultdict
from shutil import copy2

# === CONFIG ===
MODEL_PATH = os.path.join("models", "cnn_model.pt")
SAVE_FIGS = True
NORMALIZE = True
MISCLASSIFIED_DIR = os.path.join("data", "misclassified")

os.makedirs(MISCLASSIFIED_DIR, exist_ok=True)

def plot_confusion(cm, class_names, title, filename, normalize=False):
    if normalize:
        cm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
        fmt = ".2f"
    else:
        fmt = "d"

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt=fmt, cmap="Blues",
                xticklabels=class_names, yticklabels=class_names)
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    if SAVE_FIGS:
        os.makedirs("models", exist_ok=True)
        plt.savefig(os.path.join("models", filename))
    plt.show()

def evaluate():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiTaskCNN()
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()

    dataset = TileDataset(DATA_DIR)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE)

    y_true_letter, y_pred_letter = [], []
    y_true_bonus, y_pred_bonus = [], []

    letter_misclassified = defaultdict(list)
    bonus_misclassified = defaultdict(list)

    with torch.no_grad():
        for i, (images, letter_labels, bonus_labels) in enumerate(loader):
            images = images.to(device)
            letter_labels = letter_labels.to(device)
            bonus_labels = bonus_labels.to(device)

            letter_logits, bonus_logits = model(images)
            letter_preds = torch.argmax(letter_logits, dim=1)
            bonus_preds = torch.argmax(bonus_logits, dim=1)

            for j in range(len(images)):
                l_true = letter_labels[j].item()
                l_pred = letter_preds[j].item()
                b_true = bonus_labels[j].item()
                b_pred = bonus_preds[j].item()

                y_true_letter.append(l_true)
                y_pred_letter.append(l_pred)
                y_true_bonus.append(b_true)
                y_pred_bonus.append(b_pred)

                if l_true != l_pred or b_true != b_pred:
                    idx = i * BATCH_SIZE + j
                    path, letter, bonus = dataset.samples[idx]
                    dst = os.path.join(MISCLASSIFIED_DIR, os.path.basename(path))
                    copy2(path, dst)
                    if l_true != l_pred:
                        letter_misclassified[index_to_letter[l_true]].append(index_to_letter[l_pred])
                    if b_true != b_pred:
                        bonus_misclassified[index_to_bonus[b_true]].append(index_to_bonus[b_pred])

    # === CONFUSION MATRICES ===
    cm_letters = confusion_matrix(y_true_letter, y_pred_letter)
    cm_bonus = confusion_matrix(y_true_bonus, y_pred_bonus)

    letter_labels = [index_to_letter[i] for i in range(26)]
    bonus_labels = [index_to_bonus[i] for i in range(5)]

    print("\n📊 Letter Confusion Matrix:")
    print(cm_letters)
    print("\n🎯 Bonus Confusion Matrix:")
    print(cm_bonus)

    plot_confusion(cm_letters, letter_labels, "Letter Confusion Matrix", "letter_confusion.png", normalize=False)
    plot_confusion(cm_letters, letter_labels, "Normalized Letter Confusion Matrix", "letter_confusion_norm.png", normalize=True)
    plot_confusion(cm_bonus, bonus_labels, "Bonus Confusion Matrix", "bonus_confusion.png", normalize=False)
    plot_confusion(cm_bonus, bonus_labels, "Normalized Bonus Confusion Matrix", "bonus_confusion_norm.png", normalize=True)

    print("\n🧠 Underperforming Letters:")
    for letter, wrong_preds in letter_misclassified.items():
        print(f"  {letter}: {len(wrong_preds)} misclassified")

    print("\n🧠 Underperforming Bonuses:")
    for bonus, wrong_preds in bonus_misclassified.items():
        print(f"  {bonus}: {len(wrong_preds)} misclassified")

if __name__ == "__main__":
    evaluate()
