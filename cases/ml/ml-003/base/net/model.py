"""Small MLP classifier. forward() returns raw logits (no softmax)."""
from __future__ import annotations

import torch
from torch import nn


class MLP(nn.Module):
    def __init__(self, n_in: int, n_classes: int, hidden: int = 128, p_drop: float = 0.2) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_in, hidden), nn.ReLU(), nn.Dropout(p_drop),
            nn.Linear(hidden, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
