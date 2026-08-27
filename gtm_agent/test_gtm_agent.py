from types import SimpleNamespace

import gtm_agent.gtm_agent as gtm_agent


def test_send_prospect_email_blocks_disqualified_prospect(monkeypatch):
    prospect_id = "LEAD-50001"
    monkeypatch.setattr(
        gtm_agent.data_service,
        "get_prospect_record",
        lambda requested_id: {"prospect_id": requested_id, "disqualified": True},
    )

    def fail_if_called():
        raise AssertionError("disqualified prospects must not generate a message ID")

    monkeypatch.setattr(gtm_agent.uuid, "uuid4", fail_if_called)

    result = gtm_agent.send_prospect_email.func(
        {"prospect_id": prospect_id, "email": "prospect@example.com"},
        "Subject",
        "Body",
        SimpleNamespace(config={}),
    )

    assert result == {
        "status": "blocked",
        "reason": "prospect is disqualified; outbound contact is suppressed",
        "prospect_id": prospect_id,
    }
    assert "message_id" not in result


def test_send_prospect_email_sends_qualified_prospect(monkeypatch):
    monkeypatch.setattr(
        gtm_agent.data_service,
        "get_prospect_record",
        lambda requested_id: {"prospect_id": requested_id, "disqualified": False},
    )

    result = gtm_agent.send_prospect_email.func(
        {
            "prospect_id": "LEAD-10001",
            "email": "prospect@example.com",
            "name": "Qualified Prospect",
        },
        "Subject",
        "Body",
        SimpleNamespace(config={}),
        from_rep={"email": "rep@example.com", "name": "Rep"},
    )

    assert result["status"] == "sent"
    assert result["message_id"].startswith("msg-")
