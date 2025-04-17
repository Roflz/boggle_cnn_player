import os
import torch
from torchvision import transforms
from PIL import Image
from model_definitions import MultiTaskCNN, index_to_letter, index_to_bonus

IMG_SIZE = 28

class Predictor:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = MultiTaskCNN().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.Grayscale(),
            transforms.ToTensor()
        ])

    def predict_letter_bonus_confidence(self, pil_img):
        image = self.transform(pil_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            letter_logits, bonus_logits = self.model(image)
            letter_probs = torch.softmax(letter_logits, dim=1)
            bonus_probs = torch.softmax(bonus_logits, dim=1)

            letter_idx = torch.argmax(letter_probs, dim=1).item()
            bonus_idx = torch.argmax(bonus_probs, dim=1).item()
            letter_conf = letter_probs[0][letter_idx].item()
            bonus_conf = bonus_probs[0][bonus_idx].item()

            letter = index_to_letter[letter_idx]
            return letter, bonus_idx, letter_conf, bonus_conf
