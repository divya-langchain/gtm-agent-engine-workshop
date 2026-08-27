import os
import sys
import types
from unittest.mock import Mock, patch
from pathlib import Path

package = types.ModuleType("gtm_agent")
package.__path__ = [str(Path(__file__).parent)]
sys.modules.setdefault("gtm_agent", package)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
from gtm_agent.gtm_agent import send_prospect_email


def test_send_prospect_email_blocks_disqualified_prospect_without_override():
    prospect = {
        "prospect_id": "LEAD-50002",
        "name": "Liam O'Brien",
        "email": "liam.obrien@meridiansystems.com",
    }

    with patch("gtm_agent.gtm_agent.data_service.get_prospect_record", return_value={"disqualified": True}), patch(
        "gtm_agent.gtm_agent.uuid.uuid4"
    ) as uuid4:
        result = send_prospect_email.func(prospect, "Subject", "Body", Mock())

    assert result == {
        "status": "blocked",
        "reason": "prospect is marked disqualified",
        "requires_confirmation": True,
    }
    uuid4.assert_not_called()


def test_send_prospect_email_allows_disqualified_prospect_with_override():
    prospect = {
        "prospect_id": "LEAD-50002",
        "name": "Liam O'Brien",
        "email": "liam.obrien@meridiansystems.com",
    }
    runtime = Mock()
    runtime.config = {"metadata": {"user_id": "rep_oadeyemi"}}
    from_rep = {"name": "Ola Adeyemi", "email": "ola.adeyemi@northpoint.com"}

    with patch("gtm_agent.gtm_agent.data_service.get_prospect_record", return_value={"disqualified": True}), patch(
        "gtm_agent.gtm_agent.uuid.uuid4"
    ) as uuid4:
        uuid4.return_value.hex = "a" * 32
        result = send_prospect_email.func(
            prospect,
            "Subject",
            "Body",
            runtime,
            from_rep=from_rep,
            override_disqualified=True,
        )

    assert result["status"] == "sent"
    assert result["message_id"] == "msg-aaaaaaaaaaaa"
    assert result["to"] == prospect["email"]
