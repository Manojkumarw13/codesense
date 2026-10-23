import uuid

from backend.app.integrations.base import BaseProviderConnector
from backend.app.integrations.registry import registry


class _StubConnector(BaseProviderConnector):
    def auth_headers(self):
        return {"Authorization": "Bearer stub"}

    def fetch_events(self, since=None, cursor=None):
        return [], None, False

    def map_to_raw_events(
        self, team_id=None, project_id=None, repo_id=None, payloads=None
    ):
        return []

    def verify_webhook_signature(self, payload, signature=None):
        return True

    def webhook_to_raw_events(self, payload):
        return []


def test_registry_register_and_get():
    registry.register("stub", _StubConnector)
    assert registry.get("stub") is _StubConnector
    assert "stub" in registry.list()


def test_base_connector_is_abstract():
    try:
        BaseProviderConnector(
            connector_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            config={},
        )
        raise AssertionError("BaseProviderConnector should not be instantiable")
    except TypeError:
        pass


def test_stub_connector_round_trip():
    conn = _StubConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config={"token": "x"},
    )
    assert conn.auth_headers() == {"Authorization": "Bearer stub"}
    events, cursor, has_more = conn.fetch_events()
    assert events == [] and cursor is None and has_more is False
    assert conn.verify_webhook_signature(b"{}", "sig") is True
