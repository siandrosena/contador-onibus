"""Gera um vídeo sintético curto, só pra smoke test do pipeline (I/O de vídeo,
tracker, escrita de CSV) sem precisar de uma câmera real ou dataset de pessoas.

Não serve pra validar acurácia de detecção — os "objetos" aqui são retângulos,
não pessoas, então o YOLO não vai detectar nada. O objetivo é só provar que o
script roda ponta a ponta sem quebrar. Pra ver contagem de verdade, use
--source apontando pra um vídeo real com pessoas.
"""

import os
import sys

import cv2
import numpy as np

WIDTH, HEIGHT, FPS, SECONDS = 320, 240, 15, 3


def main(output_path="sample_data/demo_smoke_test.mp4"):
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        print(f"Não consegui abrir o VideoWriter pra: {output_path}", file=sys.stderr)
        sys.exit(1)

    total_frames = FPS * SECONDS
    for i in range(total_frames):
        frame = np.full((HEIGHT, WIDTH, 3), 30, dtype=np.uint8)
        x = int((i / total_frames) * WIDTH)
        cv2.rectangle(frame, (x, 80), (x + 20, 160), (255, 255, 255), -1)
        writer.write(frame)

    writer.release()
    print(f"Vídeo sintético salvo em: {output_path}")


if __name__ == "__main__":
    main()
