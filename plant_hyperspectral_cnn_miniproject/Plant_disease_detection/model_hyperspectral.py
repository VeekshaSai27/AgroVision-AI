# model_hyperspectral.py
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")  # render without display
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ✅ Tiny model, light on CPU
import ollama


# ======================
# Dataset + CNN Model
# ======================
class HyperspectralDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

    def __len__(self):
        return len(self.X)


class PixelCNN(nn.Module):
    def __init__(self, in_channels, num_classes):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 16, 3, padding=1)
        self.conv2 = nn.Conv1d(16, 32, 3, padding=1)
        self.fc1 = nn.Linear(32 * in_channels, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = x.unsqueeze(1)
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)


# ======================
# Training & Evaluation
# ======================
def train_model(model, loader, criterion, optimizer, epochs=20):
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for inputs, labels in loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(loader):.4f}")


def evaluate(model, loader):
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            out = model(x)
            _, p = torch.max(out, 1)
            preds.append(p.cpu().numpy())
            labels.append(y.cpu().numpy())
    preds = np.concatenate(preds)
    labels = np.concatenate(labels)
    return accuracy_score(labels, preds)


# ======================
# Indices & Visualization
# ======================
def compute_ndvi(image, nir_idx, red_idx):
    nir, red = image[:, :, nir_idx], image[:, :, red_idx]
    return (nir - red) / (nir + red + 1e-8)


def compute_lci(image, nir_idx, green_idx):
    nir, green = image[:, :, nir_idx], image[:, :, green_idx]
    return (nir - green) / (nir + green + 1e-8)


def predict_full_image(model, data_image, mask_valid):
    model.eval()
    H, W, C = data_image.shape
    flat = data_image[mask_valid].reshape(-1, C)
    flat_t = torch.tensor(flat, dtype=torch.float32)
    with torch.no_grad():
        p = model(flat_t)
        p = torch.argmax(p, dim=1).cpu().numpy()
    full = np.zeros((H * W), dtype=np.uint8)
    full[mask_valid.flatten()] = p
    return full.reshape(H, W)


def visualize_overlay(ndvi, lci, prediction_map, out_path):
    vegetation_mask = (prediction_map == 0) if prediction_map is not None else np.ones_like(ndvi, dtype=bool)

    ndvi_veg = np.zeros_like(ndvi)
    lci_veg = np.zeros_like(lci)
    ndvi_veg[vegetation_mask] = ndvi[vegetation_mask]
    lci_veg[vegetation_mask] = lci[vegetation_mask]

    fig, axs = plt.subplots(1, 3, figsize=(16, 5))
    if prediction_map is not None:
        axs[0].imshow(prediction_map, cmap="jet")
        axs[0].set_title("Predicted Classes")
    else:
        axs[0].imshow(ndvi, cmap="YlGn")
        axs[0].set_title("NDVI")

    im1 = axs[1].imshow(ndvi_veg, cmap="YlGn")
    axs[1].set_title("NDVI (vegetation only)")
    plt.colorbar(im1, ax=axs[1])

    im2 = axs[2].imshow(lci_veg, cmap="YlOrRd")
    axs[2].set_title("LCI (vegetation only)")
    plt.colorbar(im2, ax=axs[2])

    for ax in axs:
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def analyze_indices(ndvi, lci):
    ndvi_mean = float(np.mean(ndvi))
    lci_mean = float(np.mean(lci))
    if ndvi_mean > 0.4 and lci_mean > 0.3:
        msg = "Vegetation healthy: strong biomass and good chlorophyll."
    elif ndvi_mean > 0.4 and lci_mean < 0.2:
        msg = "Good structure but low chlorophyll — possible nutrient deficiency."
    elif ndvi_mean < 0.3 and lci_mean < 0.2:
        msg = "Sparse & low chlorophyll — stress, bare soil, or senescence."
    else:
        msg = "Mixed vegetation health detected."
    return ndvi_mean, lci_mean, msg


# ======================
# Full Analysis
# ======================
def run_hyperspectral_analysis(data_path: str, label_path: str | None, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    data = np.load(data_path)
    data = (data - data.min()) / (data.max() - data.min() + 1e-12)
    H, W, C = data.shape

    acc = None
    pred_map = None

    if label_path:
        labels = np.load(label_path)
        X = data.reshape(-1, C)
        y = labels.reshape(-1)
        mask = y > 0
        X, y = X[mask], y[mask] - 1
        num_classes = int(np.max(y) + 1)

        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        tr_loader = DataLoader(HyperspectralDataset(torch.tensor(Xtr, dtype=torch.float32), torch.tensor(ytr, dtype=torch.long)), batch_size=64, shuffle=True)
        te_loader = DataLoader(HyperspectralDataset(torch.tensor(Xte, dtype=torch.float32), torch.tensor(yte, dtype=torch.long)), batch_size=64)

        model = PixelCNN(in_channels=C, num_classes=num_classes)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=1e-3)
        train_model(model, tr_loader, criterion, optimizer, epochs=20)
        acc = evaluate(model, te_loader)

        valid_mask = labels > 0
        pred_map = predict_full_image(model, data, valid_mask)

    ndvi = compute_ndvi(data, nir_idx=min(48, C-1), red_idx=min(29, C-1))
    lci = compute_lci(data, nir_idx=min(48, C-1), green_idx=min(19, C-1))

    plot_file = "visualization_output.png"
    plot_path = os.path.join(out_dir, plot_file)
    visualize_overlay(ndvi, lci, pred_map, plot_path)

    ndvi_mean, lci_mean, analysis_text = analyze_indices(ndvi, lci)

    # TinyLlama Summary
    prompt = f"""
You are an agricultural expert. Analyze the following:
- NDVI mean: {ndvi_mean:.3f}
- LCI mean: {lci_mean:.3f}
- Health summary: {analysis_text}
- Accuracy: {acc if acc else 'N/A'}

Return JSON with:
problem_detected, severity_level, summary, and recommendations.
"""

    ai_summary = None
    try:
        resp = ollama.chat(model="tinyllama:1.1b", messages=[{"role": "user", "content": prompt.strip()}])
        text = resp["message"]["content"]
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            ai_summary = json.loads(text[s:e+1])
        else:
            ai_summary = {"summary": text.strip()}
    except Exception as e:
        ai_summary = {"error": f"AI summary failed: {e}"}

    return {
        "shape": [H, W, C],
        "accuracy": float(acc) if acc else None,
        "ndvi_mean": ndvi_mean,
        "lci_mean": lci_mean,
        "analysis_text": analysis_text,
        "plot_file": plot_file,
        "ai_summary": ai_summary
    }
