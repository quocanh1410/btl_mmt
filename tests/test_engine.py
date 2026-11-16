from tcpfc.engine import Simulator


def test_events_run_in_time_order():
    sim, log = Simulator(), []
    sim.schedule(2.0, log.append, "b")
    sim.schedule(1.0, log.append, "a")
    sim.run()
    assert log == ["a", "b"] and sim.now == 2.0


def test_same_time_is_fifo():
    sim, log = Simulator(), []
    for x in "xyz":
        sim.schedule(1.0, log.append, x)
    sim.run()
    assert log == list("xyz")


def test_cancel():
    sim, log = Simulator(), []
    h = sim.schedule(1.0, log.append, "no")
    sim.cancel(h)
    sim.run()
    assert log == []


def test_run_until():
    sim, log = Simulator(), []
    sim.schedule(5.0, log.append, "late")
    sim.run(until=1.0)
    assert log == [] and sim.now == 1.0
