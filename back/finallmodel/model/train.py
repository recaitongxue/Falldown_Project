import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from config import ModelConfig
from dataset_loader import SequenceSampleDataset
from network import FallActionGRU
from pose_features import PoseExtractor


def get_device(name: str) -> torch.device:
    if name == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, total_correct, total = 0.0, 0, 0
    with torch.no_grad():
        for x, y in loader:
            x = x.float().to(device)
            y = y.to(device)
            logits = model(x)
            loss = criterion(logits, y)
            total_loss += loss.item() * x.size(0)
            pred = logits.argmax(dim=1)
            total_correct += (pred == y).sum().item()
            total += x.size(0)
    return total_loss / max(total, 1), total_correct / max(total, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_root", type=str, default="dataset")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()

    cfg = ModelConfig(dataset_root=args.dataset_root, epochs=args.epochs, batch_size=args.batch_size, device=args.device)
    device = get_device(cfg.device)
    print(f"Using device: {device}")
    pose_extractor = PoseExtractor()

    print("Building datasets (this may take a while on Windows)...", flush=True)
    train_set = SequenceSampleDataset(cfg, cfg.train_split, pose_extractor)
    val_set = SequenceSampleDataset(cfg, cfg.val_split, pose_extractor)
    print(f"Train windows: {len(train_set)}, Val windows: {len(val_set)}")
    train_loader = DataLoader(train_set, batch_size=cfg.batch_size, shuffle=True, num_workers=cfg.num_workers)
    val_loader = DataLoader(val_set, batch_size=cfg.batch_size, shuffle=False, num_workers=cfg.num_workers)

    model = FallActionGRU(
        input_size=33 * 2 + 3,
        hidden_size=cfg.hidden_size,
        num_layers=cfg.num_layers,
        num_classes=max(cfg.class_names.__len__(), 7),
        dropout=cfg.dropout,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)

    best_acc = -1.0
    Path(cfg.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    for epoch in range(cfg.epochs):
        model.train()
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{cfg.epochs}")
        for x, y in pbar:
            x = x.float().to(device)
            y = y.to(device)
            logits = model(x)
            loss = criterion(logits, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        print(f"[VAL] loss={val_loss:.4f} acc={val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            save_path = Path(cfg.checkpoint_dir) / "best_gru.pt"
            torch.save({"state_dict": model.state_dict(), "val_acc": val_acc}, save_path)
            print(f"Saved best checkpoint to {save_path}")

    print("Training done.")


if __name__ == "__main__":
    main()
