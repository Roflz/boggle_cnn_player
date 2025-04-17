import os
import torch
import torch.nn as nn
import torch.optim as optim
import json
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset
from sklearn.metrics import confusion_matrix
import seaborn as sns

from evaluate_model import evaluate
from priority_sampler import get_sample_weights
from model_definitions import (
    AugmentedTileDataset, MultiTaskCNN,
    letter_to_index, bonus_to_index,
    IMG_SIZE, DATA_DIR, BATCH_SIZE, index_to_bonus, index_to_letter
)

# === FILE PATHS ===
MODEL_PATH = os.path.join("models", "cnn_model.pt")
CONFIG_PATH = os.path.join("models", "model_config.json")
EPOCHS = 100
LEARNING_RATE = 0.001

# === TRAINING LOOP ===
def train():
    full_dataset = AugmentedTileDataset(DATA_DIR)
    indices = list(range(len(full_dataset)))
    train_idx, val_idx = train_test_split(indices, test_size=0.2, random_state=42)

    train_dataset = Subset(full_dataset, train_idx)
    val_dataset = Subset(full_dataset, val_idx)

    print(f"\n🧪 Training set size: {len(train_dataset)} tiles")
    print(f"🧪 Validation set size: {len(val_dataset)} tiles")

    train_sampler = get_sample_weights(train_dataset)
    val_sampler = get_sample_weights(val_dataset)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=train_sampler)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, sampler=val_sampler)

    model = MultiTaskCNN()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    best_loss = float('inf')
    best_state = None
    best_epoch = -1
    train_losses = []
    val_losses = []

    print(f"\n🎯 Starting training for {EPOCHS} epochs...")
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for images, letter_labels, bonus_labels in train_loader:
            images = images.to(device)
            letter_labels = letter_labels.to(device)
            bonus_labels = bonus_labels.to(device)

            optimizer.zero_grad()
            letter_logits, bonus_logits = model(images)
            loss1 = criterion(letter_logits, letter_labels)
            loss2 = criterion(bonus_logits, bonus_labels)
            loss = loss1 + loss2
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        train_losses.append(total_loss)

        # Validation loss
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, letter_labels, bonus_labels in val_loader:
                images = images.to(device)
                letter_labels = letter_labels.to(device)
                bonus_labels = bonus_labels.to(device)

                letter_logits, bonus_logits = model(images)
                loss1 = criterion(letter_logits, letter_labels)
                loss2 = criterion(bonus_logits, bonus_labels)
                val_loss += (loss1 + loss2).item()

        val_losses.append(val_loss)
        print(f"Epoch {epoch+1:3d}/{EPOCHS} | Train Loss: {total_loss:.4f} | Val Loss: {val_loss:.4f}")

        if val_loss < best_loss:
            best_loss = val_loss
            best_state = model.state_dict()
            best_epoch = epoch

    # Only save the best model based on validation loss
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if best_state is not None:
        torch.save(best_state, MODEL_PATH)

    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "input_size": IMG_SIZE,
            "letter_classes": len(letter_to_index),
            "bonus_classes": len(bonus_to_index)
        }, f)

    print(f"\n✅ Best model saved based on lowest *validation* loss (Epoch {best_epoch+1}) with loss {best_loss:.4f}")

    # Plot training vs validation loss
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label="Training Loss", color="blue")
    plt.plot(val_losses, label="Validation Loss", color="orange")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training vs Validation Loss")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    loss_plot_path = "models/loss_curve.png"
    plt.savefig(loss_plot_path)
    plt.show()

    print(f"\n📉 Saved training/validation loss graph to: {loss_plot_path}")

    # Post-training evaluation on validation set only
    print("🔍 Running post-training evaluation on validation set...")
    evaluate(dataset=val_dataset)

    # === Confusion Matrices for Validation ===
    all_true_letters = []
    all_pred_letters = []
    all_true_bonus = []
    all_pred_bonus = []

    model.eval()
    with torch.no_grad():
        for images, letter_labels, bonus_labels in val_loader:
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

    # Plot confusion matrices
    letter_conf_matrix = confusion_matrix(all_true_letters, all_pred_letters)
    bonus_conf_matrix = confusion_matrix(all_true_bonus, all_pred_bonus)

    # Plot confusion matrices
    plt.figure(figsize=(12, 6))

    # Plot Letter Confusion Matrix
    plt.subplot(1, 2, 1)
    sns.heatmap(letter_conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=[index_to_letter[i] for i in range(26)], yticklabels=[index_to_letter[i] for i in range(26)])
    plt.title("Letter Classification Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")

    # Plot Bonus Confusion Matrix
    plt.subplot(1, 2, 2)
    sns.heatmap(bonus_conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=[index_to_bonus[i] for i in range(5)], yticklabels=[index_to_bonus[i] for i in range(5)])
    plt.title("Bonus Classification Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")

    plt.tight_layout()
    cm_plot_path = "models/confusion_matrices.png"
    plt.savefig(cm_plot_path)
    plt.show()

    print(f"📊 Confusion matrices saved to: {cm_plot_path}")

if __name__ == "__main__":
    train()
