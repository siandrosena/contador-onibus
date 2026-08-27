"""CLI: conta pessoas cruzando uma linha em um vídeo, usando YOLOv8 + ByteTrack.

Exemplo:
    python src/counter.py --source video.mp4 --line 0,0.5,1,0.5 --save-video
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

import cv2
from ultralytics import YOLO

from crossing import LineCounter

PERSON_CLASS_ID = 0  # classe "person" no COCO, usada pelos pesos padrão do YOLOv8


def parse_line_arg(line_arg, width, height):
    """Converte "x1,y1,x2,y2" (em razão 0-1 ou pixels) nos dois pontos da linha."""
    x1, y1, x2, y2 = (float(v) for v in line_arg.split(","))
    if max(x1, y1, x2, y2) <= 1.0:
        x1, x2 = x1 * width, x2 * width
        y1, y2 = y1 * height, y2 * height
    return (x1, y1), (x2, y2)


def parse_hhmm(value):
    return datetime.strptime(value, "%H:%M")


def build_arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Caminho do vídeo de entrada")
    parser.add_argument("--model", default="yolov8n.pt", help="Pesos do YOLOv8 (baixa automático se não existir)")
    parser.add_argument(
        "--line",
        default="0,0.5,1,0.5",
        help="Linha de contagem 'x1,y1,x2,y2'. Valores <=1 são tratados como razão do frame.",
    )
    parser.add_argument("--conf", type=float, default=0.35, help="Confiança mínima de detecção")
    parser.add_argument("--output", default="outputs/log.csv", help="CSV de saída dos eventos")
    parser.add_argument("--save-video", action="store_true", help="Salva vídeo anotado em outputs/annotated.mp4")
    parser.add_argument(
        "--video-start-time",
        default=None,
        help="Horário real (HH:MM) do início do vídeo, pra calcular timestamp dos eventos",
    )
    parser.add_argument("--window-start", default=None, help="Só loga eventos a partir deste horário (HH:MM)")
    parser.add_argument("--window-end", default=None, help="Só loga eventos até este horário (HH:MM)")
    return parser


def in_time_window(event_time, window_start, window_end):
    if window_start is None or window_end is None:
        return True
    t = event_time.time()
    start, end = window_start.time(), window_end.time()
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end  # janela cruzando meia-noite (ex.: 20:30-24:30)


def run(args):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Vídeo não encontrado: {source_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(source_path))
    if not cap.isOpened():
        print(f"Não consegui abrir o vídeo: {source_path}", file=sys.stderr)
        return 1

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()

    line_p1, line_p2 = parse_line_arg(args.line, width, height)
    counter = LineCounter(line_p1=line_p1, line_p2=line_p2)

    video_start = parse_hhmm(args.video_start_time) if args.video_start_time else None
    window_start = parse_hhmm(args.window_start) if args.window_start else None
    window_end = parse_hhmm(args.window_end) if args.window_end else None

    writer = None
    if args.save_video:
        annotated_path = output_path.parent / "annotated.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(annotated_path), fourcc, fps, (width, height))

    model = YOLO(args.model)
    logged_events = []

    results = model.track(
        source=str(source_path),
        classes=[PERSON_CLASS_ID],
        conf=args.conf,
        tracker="bytetrack.yaml",
        persist=True,
        stream=True,
        verbose=False,
    )

    frame_idx = 0
    for result in results:
        tracked_objects = []
        if result.boxes is not None and result.boxes.id is not None:
            for box, track_id in zip(result.boxes.xyxy.tolist(), result.boxes.id.tolist()):
                x1, y1, x2, y2 = box
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                tracked_objects.append((int(track_id), cx, cy))

        events = counter.update(tracked_objects, frame_idx)

        for event in events:
            elapsed = timedelta(seconds=frame_idx / fps)
            event_time = (video_start + elapsed) if video_start else None
            if event_time is None or in_time_window(event_time, window_start, window_end):
                logged_events.append(
                    {
                        "timestamp": event_time.strftime("%H:%M:%S") if event_time else f"{elapsed}",
                        "evento": event.direction,
                        "track_id": event.track_id,
                        "contagem_total": counter.total_count,
                    }
                )

        if writer is not None:
            frame = result.plot()
            cv2.line(frame, tuple(map(int, line_p1)), tuple(map(int, line_p2)), (0, 0, 255), 2)
            writer.write(frame)

        frame_idx += 1

    if writer is not None:
        writer.release()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer_csv = csv.DictWriter(f, fieldnames=["timestamp", "evento", "track_id", "contagem_total"])
        writer_csv.writeheader()
        writer_csv.writerows(logged_events)

    print(f"Frames processados: {frame_idx}")
    print(f"Total de pessoas contadas: {counter.total_count}")
    print(f"Log salvo em: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run(build_arg_parser().parse_args()))
