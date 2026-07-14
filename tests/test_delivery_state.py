from datetime import date

from agent_notice.delivery_state import DeliveryState


def test_delivery_state_marks_date_and_prevents_second_send(tmp_path):
    state = DeliveryState.load(tmp_path / "delivery.json")
    today = date(2026, 7, 14)
    assert not state.was_delivered(today)
    state.mark_delivered(today)
    state.save(tmp_path / "delivery.json")
    assert DeliveryState.load(tmp_path / "delivery.json").was_delivered(today)
