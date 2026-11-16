"""P4 viết."""
import pytest

from tcpfc.metrics import Metrics


@pytest.mark.todo
def test_time_weighted_mean_step_function():
    # giá trị 0 trong [0,1), 10 trong [1,3) -> trung bình trên [0,3] = 20/3
    s = [(0.0, 0), (1.0, 10)]
    assert Metrics.time_weighted_mean(s, 3.0) == pytest.approx(20 / 3)


@pytest.mark.todo
def test_completion_time_and_goodput():
    m = Metrics(total_bytes=1000, buffer_size=4000)
    m.on_app_read(1.0, 500)
    m.on_app_read(2.0, 500)
    out = m.summary()
    assert out["completion_time"] == pytest.approx(2.0)
    assert out["goodput"] == pytest.approx(500.0)
