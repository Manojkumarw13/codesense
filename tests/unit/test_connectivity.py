from backend.app.core.connectivity import (
    InternetState,
    get_internet_state,
    reset_connectivity_cache,
)


def test_offline_when_probe_fails():
    reset_connectivity_cache()
    assert get_internet_state(probe=lambda: False) is InternetState.OFFLINE


def test_online_when_probe_succeeds():
    reset_connectivity_cache()
    assert get_internet_state(probe=lambda: True) is InternetState.ONLINE


def test_state_is_cached_between_calls():
    reset_connectivity_cache()
    calls = []

    def probe() -> bool:
        calls.append(1)
        return True

    assert get_internet_state(probe=probe) is InternetState.ONLINE
    assert get_internet_state(probe=probe) is InternetState.ONLINE
    assert len(calls) == 1


def test_force_bypasses_cache():
    reset_connectivity_cache()
    calls = []

    def probe() -> bool:
        calls.append(1)
        return False

    get_internet_state(probe=probe)
    get_internet_state(probe=probe, force=True)
    assert len(calls) == 2
