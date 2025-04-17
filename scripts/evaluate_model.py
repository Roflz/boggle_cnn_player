from sklearn.metrics import classification_report
from model_definitions import (
    letter_to_index, index_to_letter,
    bonus_to_index, index_to_bonus,
    MultiTaskCNN, IMG_SIZE
)
from sklearn.metrics import classification_report
from model_definitions import (
    letter_to_index, index_to_letter,
    bonus_to_index, index_to_bonus,
    MultiTaskCNN, IMG_SIZE
)
from torch.utils.data import DataLoader
import torch
import os

# Default evaluation directory
EVAL_DATA_DIR = os.path.join("data", "boggle_tiles")

@torch.no_grad()
def evaluate(dataset=None, batch_size=64):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if dataset is None:
        from model_definitions import TileDataset
        dataset = TileDataset(EVAL_DATA_DIR)

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    model = MultiTaskCNN().to(device)
    model.load_state_dict(torch.load("models/cnn_model.pt", map_location=device))
    model.eval()

    all_true_letters = []
    all_pred_letters = []
    all_true_bonus = []
    all_pred_bonus = []

    for images, letter_labels, bonus_labels in loader:
        images = images.to(device)
        letter_labels = letter_labels.to(device)
        bonus_labels = bonus_labels.to(device)

        letter_logits, bonus_logits = model(images)
        letter_preds = torch.argmax(letter_logits, dim=1)
        bonus_preds = torch.argmax(bonus_logits, dim=1)

        all_true_letters.extend(letter_labels.cpu().tolist())
        all_pred_letters.extend(letter_preds.cpu().tolist())
        all_true_bonus.extend(bonus_labels.cpu().tolist())
        all_pred_bonus.extend(bonus_preds.cpu().tolist())

    # === LETTER REPORT ===
    letter_labels = sorted(index_to_letter.keys())
    print("\n===== LETTER CLASSIFICATION REPORT =====")
    print(classification_report(
        all_true_letters, all_pred_letters,
        labels=letter_labels,
        target_names=[index_to_letter[i] for i in letter_labels]
    ))

    # === BONUS REPORT ===
    bonus_labels = sorted(index_to_bonus.keys())
    print("\n===== BONUS CLASSIFICATION REPORT =====")
    print(classification_report(
        all_true_bonus, all_pred_bonus,
        labels=bonus_labels,
        target_names=[index_to_bonus[i] for i in bonus_labels]
    ))

    # Check if any classes are missing from the validation set
    missing_letters = set(letter_labels) - set(all_true_letters)
    missing_bonus = set(bonus_labels) - set(all_true_bonus)

    if missing_letters:
        print(f"⚠️ Missing letters in validation set: {missing_letters}")
    if missing_bonus:
        print(f"⚠️ Missing bonus classes in validation set: {missing_bonus}")

