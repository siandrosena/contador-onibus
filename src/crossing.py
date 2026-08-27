"""Lógica pura de cruzamento de linha e deduplicação de ID.

Isolada do pipeline de vídeo/YOLO de propósito: são as duas partes do
sistema com regra de negócio (não só chamada de biblioteca), então são
as que valem a pena testar sem precisar rodar detecção de verdade.
"""

from dataclasses import dataclass, field


def _side(line_p1, line_p2, point):
    """Sinal do produto vetorial: de que lado da linha o ponto está.

    >0 de um lado, <0 do outro, 0 em cima da linha.
    """
    (x1, y1), (x2, y2) = line_p1, line_p2
    px, py = point
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


@dataclass
class CrossingEvent:
    track_id: int
    direction: str  # "entrada" ou "saida"
    frame_idx: int


@dataclass
class LineCounter:
    """Conta cruzamentos de uma linha por objetos rastreados (por ID).

    line_p1/line_p2: dois pontos (x, y) que definem a linha de contagem.
    max_reassign_dist: distância máxima (px) pra considerar que um ID novo
        é a continuação de um ID perdido recentemente (troca de ID do tracker).
    max_reassign_gap: nº máximo de frames entre o ID sumir e o novo aparecer
        pra ainda considerar continuação.
    """

    line_p1: tuple
    line_p2: tuple
    max_reassign_dist: float = 60.0
    max_reassign_gap: int = 15

    _last_side: dict = field(default_factory=dict)
    _last_seen: dict = field(default_factory=dict)  # id -> (cx, cy, frame_idx)
    _counted_ids: set = field(default_factory=set)
    _lost_tracks: dict = field(default_factory=dict)  # id -> (cx, cy, frame_idx, counted)
    _id_aliases: dict = field(default_factory=dict)  # id do tracker -> id "canônico"

    def _resolve_id(self, raw_id, centroid, frame_idx):
        """Resolve o ID do tracker pro ID canônico, remapeando em caso de troca."""
        if raw_id in self._id_aliases:
            return self._id_aliases[raw_id]
        if raw_id in self._last_side:
            return raw_id

        best_match, best_dist = None, None
        for lost_id, (lx, ly, lframe, _counted) in self._lost_tracks.items():
            if frame_idx - lframe > self.max_reassign_gap:
                continue
            dist = ((centroid[0] - lx) ** 2 + (centroid[1] - ly) ** 2) ** 0.5
            if dist <= self.max_reassign_dist and (best_dist is None or dist < best_dist):
                best_match, best_dist = lost_id, dist

        if best_match is not None:
            self._id_aliases[raw_id] = best_match
            del self._lost_tracks[best_match]
            return best_match

        return raw_id

    def update(self, tracked_objects, frame_idx):
        """Processa um frame. tracked_objects: iterável de (raw_id, cx, cy).

        Retorna lista de CrossingEvent gerados neste frame.
        """
        events = []
        seen_this_frame = set()

        for raw_id, cx, cy in tracked_objects:
            canonical_id = self._resolve_id(raw_id, (cx, cy), frame_idx)
            seen_this_frame.add(canonical_id)
            self._last_seen[canonical_id] = (cx, cy, frame_idx)

            side = _side(self.line_p1, self.line_p2, (cx, cy))
            prev_side = self._last_side.get(canonical_id)
            self._last_side[canonical_id] = side

            if prev_side is None or side == 0 or prev_side == 0:
                continue

            crossed = (prev_side > 0) != (side > 0)
            if crossed and canonical_id not in self._counted_ids:
                direction = "entrada" if side > 0 else "saida"
                self._counted_ids.add(canonical_id)
                events.append(CrossingEvent(canonical_id, direction, frame_idx))

        # IDs que sumiram neste frame viram candidatos a "troca de ID"
        for tracked_id in list(self._last_seen.keys()):
            if tracked_id not in seen_this_frame:
                cx, cy, last_frame = self._last_seen[tracked_id]
                if frame_idx - last_frame == 1:
                    self._lost_tracks[tracked_id] = (
                        cx, cy, last_frame, tracked_id in self._counted_ids
                    )

        return events

    @property
    def total_count(self):
        return len(self._counted_ids)
