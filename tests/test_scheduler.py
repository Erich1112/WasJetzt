import pytest

from wasjetzt.services.scheduler import SchedulerCore


class Clock:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t

    def advance(self, seconds, step=10):
        """Generator: avansează ceasul în pași (ca timer-ul real); apelantul face tick() la fiecare pas."""
        end = self.t + seconds
        while self.t < end:
            self.t = min(self.t + step, end)
            yield


def test_first_prompt_after_interval():
    clock = Clock()
    core = SchedulerCore(interval_minutes=5, now=clock)
    for _ in clock.advance(5 * 60 - 10):
        assert core.tick() is False
    clock.t += 10
    assert core.tick() is True and core.prompt_open and core.prompt_source == "scheduled"


def test_interval_change_reschedules():
    clock = Clock()
    core = SchedulerCore(interval_minutes=60, now=clock)
    for _ in clock.advance(600):
        core.tick()
    core.set_interval(5)
    assert core.next_due == pytest.approx(clock.t + 300)
    with pytest.raises(ValueError):
        core.set_interval(4)
    with pytest.raises(ValueError):
        core.set_interval(1441)


def test_no_two_windows_at_once():
    clock = Clock()
    core = SchedulerCore(interval_minutes=5, now=clock)
    for _ in clock.advance(300):
        core.tick()
    assert core.prompt_open
    assert core.begin_prompt("manual") is False
    shown_again = 0
    for _ in clock.advance(1200):  # fereastra rămâne deschisă 20 de minute
        shown_again += core.tick()
    assert shown_again == 0


def test_dismiss_without_answer_waits_next_interval():
    clock = Clock()
    core = SchedulerCore(interval_minutes=10, on_dismiss="wait_next_interval", now=clock)
    for _ in clock.advance(600):
        core.tick()
    assert core.prompt_open
    core.end_prompt(answered=False)
    assert core.next_due == pytest.approx(clock.t + 600)
    assert not core.prompt_open


def test_retry_soon_is_bounded_not_a_loop():
    clock = Clock()
    core = SchedulerCore(interval_minutes=60, on_dismiss="retry_soon", retry_minutes=5, max_retries=3, now=clock)
    times = []
    for _ in clock.advance(6 * 3600):  # utilizatorul închide MEREU fereastra fără răspuns
        if core.tick():
            times.append(clock.t)
            core.end_prompt(answered=False)
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert all(g >= 300 for g in gaps)  # niciodată în buclă rapidă
    # tipar: prima la 60 min, apoi cel mult 3 reîncercări la 5 min, apoi din nou interval întreg
    assert gaps[:4] == [300, 300, 300, 3600]


def test_dismiss_does_not_create_record_in_scheduler_state():
    clock = Clock()
    core = SchedulerCore(interval_minutes=5, now=clock)
    for _ in clock.advance(300):
        core.tick()
    core.end_prompt(answered=False)
    assert core.prompt_open is False  # închiderea fără răspuns nu produce nicio înregistrare (stratul DB nu e apelat)


def test_sleep_resume_does_not_burst():
    clock = Clock()
    core = SchedulerCore(interval_minutes=5, now=clock)
    for _ in clock.advance(120):
        core.tick()
    clock.t += 8 * 3600  # calculatorul a dormit 8 ore (ar fi fost 96 de întrebări ratate)
    assert core.tick() is False and core.resume_events == 1
    assert core.next_due == pytest.approx(clock.t + 300)
    shown = 0
    for _ in clock.advance(299):
        shown += core.tick()
    assert shown == 0
    clock.t += 10
    assert core.tick() is True  # exact una, la intervalul normal
    assert core.tick() is False


def test_manual_prompt_does_not_move_schedule():
    clock = Clock()
    core = SchedulerCore(interval_minutes=60, now=clock)
    due = core.next_due
    clock.t += 100
    assert core.begin_prompt("manual") is True
    core.end_prompt(answered=True)
    assert core.next_due == due


def test_pause_blocks_prompts_and_resume_reschedules():
    clock = Clock()
    core = SchedulerCore(interval_minutes=5, now=clock)
    core.pause()
    shown = 0
    for _ in clock.advance(1800):
        shown += core.tick()
    assert shown == 0
    core.resume()
    assert core.next_due == pytest.approx(clock.t + 300)
