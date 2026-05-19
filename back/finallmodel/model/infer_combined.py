import argparse
import os
from collections import deque

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

from config import ModelConfig, RuleConfig
from network import FallActionGRU
from pose_features import FallRuleEngine, PoseExtractor


def get_font(font_size=20):
    font_paths = [
        "/Windows/Fonts/simhei.ttf",
        "/Windows/Fonts/msyh.ttc",
        "simhei.ttf",
        "msyh.ttc",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
    return ImageFont.load_default()


def draw_text_cn(frame, text, x, y, color=(0, 255, 0), font_size=20):
    font = get_font(font_size)
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text((x, y), text, font=font, fill=(color[2], color[1], color[0]))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def load_model(ckpt_path, cfg, device):
    model = FallActionGRU(
        input_size=33 * 2 + 3,
        hidden_size=cfg.hidden_size,
        num_layers=cfg.num_layers,
        num_classes=len(cfg.class_names),
        dropout=cfg.dropout,
    ).to(device)
    state = torch.load(ckpt_path, map_location=device, weights_only=True)
    model.load_state_dict(state["state_dict"], strict=False)
    model.eval()
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, required=True, help="视频文件路径")
    parser.add_argument("--ckpt", type=str, default="checkpoints/best_gru.pt", help="模型权重路径")
    parser.add_argument("--save", type=str, default="", help="保存结果视频路径")
    parser.add_argument("--show-skeleton", action="store_true", default=True, help="显示骨骼姿态标注")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model_cfg = ModelConfig(device=device)
    rule_cfg = RuleConfig(
        fps=20.0,
        cgdd_frame_gap=5,
        v_cr=0.015,      # 论文典型值: 0.01-0.02
        theta_cr_deg=55.0,  # 论文典型值: 45-60度
        p_cr=1.2,        # 论文典型值: 1.0-1.5
        t_cr_sec=3.0     # 论文典型值: 2-5秒
    )

    model = load_model(args.ckpt, model_cfg, device)
    pose = PoseExtractor()
    rule = FallRuleEngine(rule_cfg)
    
    seq = deque(maxlen=model_cfg.sequence_length)

    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        print(f"无法打开视频: {args.source}")
        return

    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(args.save, fourcc, fps, (w, h))

    frame_idx = 0
    fall_detected = False
    detected_class = "unknown"
    class_prob = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame_idx += 1
        feat = pose.extract(frame)

        if feat is None:
            frame = draw_text_cn(frame, "未检测到人体", 20, 30, (0, 0, 255), 24)
        else:
            # 绘制骨骼姿态标注
            if args.show_skeleton:
                frame = pose.draw_skeleton(frame, feat)
            
            vec = np.concatenate(
                [
                    feat.keypoints.reshape(-1).astype(np.float32),
                    np.array([feat.center_y, feat.tilt_deg / 180.0, feat.wh_ratio], dtype=np.float32),
                ],
                axis=0,
            )
            seq.append(vec)
            
            rule_result = rule.update(feat)
            M1 = bool(rule_result["M1"])
            M2 = bool(rule_result["M2"])
            M3 = bool(rule_result["M3"])
            M4 = bool(rule_result["M4"])
            M5 = bool(rule_result["M5"])
            rule_fall = rule_result["fall_rule"]
            alert = rule_result["alert"]

            if len(seq) == model_cfg.sequence_length:
                x = torch.from_numpy(np.stack(seq).astype(np.float32)).unsqueeze(0).to(device)
                with torch.no_grad():
                    logits = model(x)
                    prob = torch.softmax(logits, dim=1)[0].cpu().numpy()
                    idx = int(prob.argmax())
                    class_prob = float(prob[idx])
                    detected_class = model_cfg.class_names[idx] if idx < len(model_cfg.class_names) else str(idx)

            combined_fall = rule_fall
            if detected_class in ["lying", "falling"] and rule_fall > 0.5:
                combined_fall = 1.0
                if not fall_detected:
                    fall_detected = True
                    print(f"\n=== 融合检测: 跌倒确认 ===")
                    print(f"帧: {frame_idx}")
                    print(f"行为识别: {detected_class} ({class_prob:.2f})")
                    print(f"规则引擎: M1={M1}, M2={M2}, M3={M3}, M4={M4}, M5={M5}")

            # 确定状态颜色和文字
            if alert > 0.5:
                color = (0, 0, 255)
                status_text = "ALERT: 跌倒告警!"
            elif combined_fall > 0.5:
                color = (0, 165, 255)
                status_text = "WARNING: 疑似跌倒"
            else:
                color = (0, 255, 0)
                status_text = f"STATUS: {detected_class}"

            # 绘制状态信息
            frame = draw_text_cn(frame, status_text, 20, 30, color, 24)
            frame = draw_text_cn(frame, f"帧: {frame_idx}", 20, 60, color, 18)
            frame = draw_text_cn(frame, f"行为: {detected_class} ({class_prob:.2f})", 20, 90, color, 16)
            
            # 绘制规则引擎状态（5个检测条件）
            frame = draw_text_cn(frame, f"M1(重心下降): {'是' if M1 else '否'}", 20, 115, color, 16)
            frame = draw_text_cn(frame, f"M2(身体倾斜): {'是' if M2 else '否'}", 20, 140, color, 16)
            frame = draw_text_cn(frame, f"M3(形状变化): {'是' if M3 else '否'}", 20, 165, color, 16)
            frame = draw_text_cn(frame, f"M4(关节角度): {'是' if M4 else '否'}", 20, 190, color, 16)
            frame = draw_text_cn(frame, f"M5(身体高度): {'是' if M5 else '否'}", 20, 215, color, 16)
            
            # 绘制关节角度信息
            frame = draw_text_cn(frame, f"肘部: {feat.elbow_angle:.1f}度", 20, 240, (255, 128, 0), 14)
            frame = draw_text_cn(frame, f"膝盖: {feat.knee_angle:.1f}度", 20, 260, (255, 128, 0), 14)
            frame = draw_text_cn(frame, f"臀部: {feat.hip_angle:.1f}度", 20, 280, (255, 128, 0), 14)

        cv2.imshow("融合跌倒检测", frame)
        if writer:
            writer.write(frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    if fall_detected:
        print("\n检测完成！视频中检测到跌倒事件")
    else:
        print("\n检测完成！视频中未检测到跌倒事件")


if __name__ == "__main__":
    main()
