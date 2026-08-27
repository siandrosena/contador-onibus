import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from crossing import LineCounter


def make_counter():
    # linha horizontal em y=100, de x=0 a x=200
    return LineCounter(line_p1=(0, 100), line_p2=(200, 100))


def test_single_crossing_counts_once():
    counter = make_counter()
    counter.update([(1, 50, 50)], frame_idx=0)   # acima da linha
    events = counter.update([(1, 50, 150)], frame_idx=1)  # cruzou pra baixo

    assert len(events) == 1
    assert counter.total_count == 1


def test_object_that_never_crosses_is_not_counted():
    counter = make_counter()
    counter.update([(1, 50, 50)], frame_idx=0)
    counter.update([(1, 55, 60)], frame_idx=1)
    counter.update([(1, 60, 70)], frame_idx=2)

    assert counter.total_count == 0


def test_same_id_does_not_double_count_on_repeated_crossing_frames():
    counter = make_counter()
    counter.update([(1, 50, 50)], frame_idx=0)
    counter.update([(1, 50, 150)], frame_idx=1)
    events = counter.update([(1, 50, 160)], frame_idx=2)  # continua do mesmo lado

    assert len(events) == 0
    assert counter.total_count == 1


def test_id_switch_after_crossing_is_not_recounted():
    """Regressão do bug que o README promete resolver: tracker perde o ID
    no meio do cruzamento e reatribui um ID novo pro mesmo objeto físico.
    """
    counter = make_counter()
    counter.update([(1, 50, 50)], frame_idx=0)
    counter.update([(1, 50, 150)], frame_idx=1)  # ID 1 cruza, é contado
    assert counter.total_count == 1

    # frame 2: tracker "perde" o ID 1 (não aparece)
    counter.update([], frame_idx=2)
    # frame 3: reaparece pertinho, como ID novo (troca de ID)
    events = counter.update([(2, 52, 152)], frame_idx=3)

    assert len(events) == 0
    assert counter.total_count == 1  # não duplicou


def test_id_switch_too_far_away_counts_as_new_object():
    counter = make_counter()
    counter.update([(1, 50, 50)], frame_idx=0)
    counter.update([(1, 50, 150)], frame_idx=1)
    counter.update([], frame_idx=2)

    # ID novo aparece longe (não é continuação), acima da linha e depois cruza
    counter.update([(2, 190, 50)], frame_idx=3)
    events = counter.update([(2, 190, 150)], frame_idx=4)

    assert len(events) == 1
    assert counter.total_count == 2


def test_id_switch_too_late_counts_as_new_object():
    counter = LineCounter(line_p1=(0, 100), line_p2=(200, 100), max_reassign_gap=2)
    counter.update([(1, 50, 50)], frame_idx=0)
    counter.update([(1, 50, 150)], frame_idx=1)
    counter.update([], frame_idx=2)
    counter.update([], frame_idx=3)
    counter.update([], frame_idx=4)
    counter.update([], frame_idx=5)

    # reaparece perto, mas depois do gap máximo -> conta como objeto novo
    events = counter.update([(2, 52, 50)], frame_idx=6)
    events += counter.update([(2, 52, 150)], frame_idx=7)

    assert len(events) == 1
    assert counter.total_count == 2


def test_direction_entrada_vs_saida():
    counter = make_counter()
    counter.update([(1, 50, 50)], frame_idx=0)
    events_in = counter.update([(1, 50, 150)], frame_idx=1)

    counter.update([(2, 50, 150)], frame_idx=2)
    events_out = counter.update([(2, 50, 50)], frame_idx=3)

    assert events_in[0].direction != events_out[0].direction
