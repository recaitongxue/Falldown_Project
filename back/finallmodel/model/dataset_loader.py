import csv
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from config import ModelConfig
from pose_features import PoseExtractor


class SequenceSampleDataset(Dataset):
    def __init__(self, cfg: ModelConfig, split: str, pose_extractor: PoseExtractor):
        self.cfg = cfg
        self.split = split
        self.pose_extractor = pose_extractor
        self.samples: List[Tuple[List[Path], List[int]]] = []
        self._feature_cache = {}
        split_root = Path(cfg.dataset_root) / split
        for seq_dir in sorted(split_root.iterdir()):
            if not seq_dir.is_dir():
                continue
            rgb_dir = seq_dir / "rgb"
            label_file = seq_dir / "labels.csv"
            if not rgb_dir.exists() or not label_file.exists():
                continue
            frame_labels = self._read_labels(label_file)
            # Windows 下逐帧调用 exists() 会非常慢，这里先一次性枚举文件名做集合判断
            rgb_files = {p.name for p in rgb_dir.glob("rgb_*.png")}
            frame_paths = []
            labels = []
            for idx, lab in frame_labels:
                name = f"rgb_{idx:04d}.png"
                if name in rgb_files:
                    frame_paths.append(rgb_dir / name)
                    labels.append(lab)
            if len(frame_paths) < cfg.sequence_length:
                continue
            for st in range(0, len(frame_paths) - cfg.sequence_length + 1, cfg.stride):
                ed = st + cfg.sequence_length
                self.samples.append((frame_paths[st:ed], labels[st:ed]))

    @staticmethod
    def _read_labels(label_file: Path) -> List[Tuple[int, int]]:
        data = []
        with label_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append((int(row["index"]), int(row["class"])))
        return data

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        frame_paths, labels = self.samples[idx]
        feats = []
        for p in frame_paths:
            key = str(p)
            if key not in self._feature_cache:
                img = cv2.imread(key)
                if img is None:
                    self._feature_cache[key] = np.zeros((33 * 2 + 3,), dtype=np.float32)
                else:
                    f = self.pose_extractor.extract(img)
                    if f is None:
                        self._feature_cache[key] = np.zeros((33 * 2 + 3,), dtype=np.float32)
                    else:
                        kp = f.keypoints.astype(np.float32).reshape(-1)
                        extra = np.array(
                            [
                                float(f.center_y),
                                float(f.tilt_deg) / 180.0,
                                float(f.wh_ratio),
                            ],
                            dtype=np.float32,
                        )
                        self._feature_cache[key] = np.concatenate([kp, extra], axis=0)
            feats.append(self._feature_cache[key])
        x = np.stack(feats, axis=0).reshape(len(feats), -1)
        # 用窗口末帧标签作为监督目标，适合在线实时推理
        y = labels[-1]
        return torch.from_numpy(x), torch.tensor(y, dtype=torch.long)
