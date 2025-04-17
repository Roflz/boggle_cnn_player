import os
import torch
import torch.nn as nn
import torch.optim as optim
import json
from torch.utils.data import DataLoader
from evaluate_model import evaluate
from priority_sampler import get_sample_weights
from model_definitions import (
    TileDataset, MultiTaskCNN,
    letter_to_index, bonus_to_index,
    IMG_SIZE, DATA_DIR, BATCH_SIZE
)

# === FILE PATHS ===
MODEL_PATH = os.path.join("models", "cnn_model.pt")
CONFIG_PATH = os.path.join("models", "model_config.json")
EPOCHS = 100
LEARNING_RATE = 0.001

# === TRAINING LOOP ===
def train():
    dataset = TileDataset(DATA_DIR)
    sampler = get_sample_weights(dataset)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, sampler=sampler)

    model = MultiTaskCNN()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for images, letter_labels, bonus_labels in loader:
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

        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {total_loss:.4f}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)

    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "input_size": IMG_SIZE,
            "letter_classes": len(letter_to_index),
            "bonus_classes": len(bonus_to_index)
        }, f)

    print("✅ Model and config saved.")

    # Auto-evaluate after training
    print("\n🔍 Running post-training evaluation...")
    evaluate()

if __name__ == "__main__":
    train()
