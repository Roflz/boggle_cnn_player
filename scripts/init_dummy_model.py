import os
import torch
import torch.nn as nn

IMG_SIZE = 28
NUM_LETTER_CLASSES = 26
NUM_BONUS_CLASSES = 5

class MultiTaskCNN(nn.Module):
    def __init__(self):
        super(MultiTaskCNN, self).__init__()
        self.shared = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten()
        )
        self.classifier_letter = nn.Sequential(
            nn.Linear(64 * (IMG_SIZE // 4) * (IMG_SIZE // 4), 128),
            nn.ReLU(),
            nn.Linear(128, NUM_LETTER_CLASSES)
        )
        self.classifier_bonus = nn.Sequential(
            nn.Linear(64 * (IMG_SIZE // 4) * (IMG_SIZE // 4), 64),
            nn.ReLU(),
            nn.Linear(64, NUM_BONUS_CLASSES)
        )

    def forward(self, x):
        shared = self.shared(x)
        return self.classifier_letter(shared), self.classifier_bonus(shared)

if __name__ == "__main__":
    model = MultiTaskCNN()
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/cnn_model.pt")
    print("✅ Dummy model saved to models/cnn_model.pt")
