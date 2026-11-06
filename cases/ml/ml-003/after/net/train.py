"""Training loop."""
from __future__ import annotations

import torch
from torch import nn
from torch.utils.data import DataLoader

from .model import MLP


def evaluate(model: MLP, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            correct += (model(xb).argmax(dim=1) == yb).sum().item()
            total += yb.numel()
    return correct / max(total, 1)


def fit(model: MLP, train_loader: DataLoader, val_loader: DataLoader, epochs: int,
        lr: float = 1e-3, device: torch.device = torch.device("cpu")) -> list[float]:
    model.to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    history = []
    for _ in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            opt.zero_grad(set_to_none=True)
        history.append(evaluate(model, val_loader, device))
    return history
