import json

from gtm_agent import gtm_agent

SENSITIVE_FIELDS = (
    "billing_qualification", "tax_id", "date_of_birth", "card_on_file",
    "credit_check_ref",
)


def test_get_prospect_returns_only_allowed_fields(monkeypatch):
    prospect_id = "LEAD-TEST"
    record = {
        "name": "Taylor Example",
        "email": "taylor@example.com",
        "disqualified": False,
        "billing_qualification": {
            "tax_id": "123-45-6789",
            "date_of_birth": "1980-01-01",
            "card_on_file": "4111111111111111",
            "credit_check_ref": "EXPN-12345",
        },
        "engagement_history": [],
        "account_details": [],
        "tech_stack": [],
    }
    monkeypatch.setattr(gtm_agent.data_service, "get_prospect_record", lambda _: record)

    result = gtm_agent.get_prospect.invoke({"prospect_id": prospect_id})

    assert result == {
        "prospect": {
            "prospect_id": prospect_id,
            "name": "Taylor Example",
            "email": "taylor@example.com",
            "disqualified": False,
        },
        "found": True,
    }
    assert all(field not in json.dumps(result) for field in SENSITIVE_FIELDS)


def test_build_prospect_profile_excludes_billing_data_and_caches_safe_profile(monkeypatch):
    prospect_id = "LEAD-TEST"
    record = {
        "name": "Taylor Example",
        "email": "taylor@example.com",
        "annual_revenue": 2500000,
        "enrichment_source": "CRM",
        "disqualified": False,
        "billing_qualification": {
            "tax_id": "123-45-6789",
            "date_of_birth": "1980-01-01",
            "card_on_file": "4111111111111111",
            "credit_check_ref": "EXPN-12345",
        },
    }
    cached = {}
    monkeypatch.setattr(gtm_agent.data_service, "get_profile_from_db", lambda _: {"prospect_profile": None})
    monkeypatch.setattr(gtm_agent.data_service, "get_prospect_record", lambda _: record)
    monkeypatch.setattr(gtm_agent.data_service, "fetch_engagement_history", lambda _: [{"channel": "email"}])
    monkeypatch.setattr(gtm_agent.data_service, "fetch_account_details", lambda _: {"industry": "Technology"})
    monkeypatch.setattr(gtm_agent.data_service, "fetch_tech_stack", lambda _: ["Python"])
    monkeypatch.setattr(gtm_agent.data_service, "save_profile_to_db", lambda _, profile: cached.update(profile))

    result = gtm_agent.build_prospect_profile.invoke({"prospect_id": prospect_id})
    profile = result["prospect_profile"]

    assert result["found"] is True
    assert profile == {
        "prospect_id": prospect_id,
        "name": "Taylor Example",
        "email": "taylor@example.com",
        "annual_revenue": 2500000,
        "enrichment_source": "CRM",
        "disqualified": False,
        "engagement_history": [{"channel": "email"}],
        "account_details": {"industry": "Technology"},
        "tech_stack": ["Python"],
    }
    assert cached == profile
    assert all(field not in json.dumps(result) for field in SENSITIVE_FIELDS)


def test_build_prospect_profile_sanitizes_cached_profile(monkeypatch):
    prospect_id = "LEAD-TEST"
    cached = {
        "prospect_id": prospect_id,
        "name": "Taylor Example",
        "email": "taylor@example.com",
        "annual_revenue": 2500000,
        "billing_qualification": {
            "tax_id": "123-45-6789",
            "date_of_birth": "1980-01-01",
            "card_on_file": "4111111111111111",
            "credit_check_ref": "EXPN-12345",
        },
        "tech_stack": ["Python"],
    }
    saved = {}
    monkeypatch.setattr(
        gtm_agent.data_service,
        "get_profile_from_db",
        lambda _: {"prospect_profile": cached},
    )
    monkeypatch.setattr(
        gtm_agent.data_service,
        "save_profile_to_db",
        lambda _, profile: saved.update(profile),
    )

    result = gtm_agent.build_prospect_profile.invoke({"prospect_id": prospect_id})

    assert result["prospect_profile"] == {
        "prospect_id": prospect_id,
        "name": "Taylor Example",
        "email": "taylor@example.com",
        "annual_revenue": 2500000,
        "tech_stack": ["Python"],
    }
    assert saved == result["prospect_profile"]
    assert all(field not in json.dumps(result) for field in SENSITIVE_FIELDS)


def test_score_prospect_filters_extra_profile_fields_from_llm_input(monkeypatch):
    prospect_profile = {
        "prospect_id": "LEAD-TEST",
        "name": "Taylor Example",
        "account_details": {"industry": "Technology"},
        "engagement_history": [{"channel": "email"}],
        "tech_stack": ["Old value"],
        "annual_revenue": 2500000,
        "enrichment_source": "CRM",
        "billing_qualification": {
            "tax_id": "123-45-6789",
            "date_of_birth": "1980-01-01",
            "card_on_file": "4111111111111111",
            "credit_check_ref": "EXPN-12345",
        },
    }
    offering = {
        "required_tech_stack": ["Python"],
        "min_annual_revenue": 1000000,
        "description": "A technology offering",
    }
    captured = {}

    class FakeLLM:
        def invoke(self, messages):
            captured["messages"] = messages
            return type("Result", (), {"model_dump": lambda self: {"score": 80}})()

    monkeypatch.setattr(gtm_agent.data_service, "fetch_tech_stack", lambda _: ["Python"])
    monkeypatch.setattr(gtm_agent, "_scoring_llm", FakeLLM())

    result = gtm_agent.score_prospect.invoke(
        {"prospect_profile": prospect_profile, "offering": offering}
    )
    scoring_input = captured["messages"][1]["content"].split("\n\nProspect profile:\n", 1)[1]

    assert result == {"score": 80}
    assert json.loads(scoring_input) == {
        "prospect_id": "LEAD-TEST",
        "name": "Taylor Example",
        "account_details": {"industry": "Technology"},
        "engagement_history": [{"channel": "email"}],
        "tech_stack": ["Python"],
        "annual_revenue": 2500000,
    }
    assert all(field not in scoring_input for field in SENSITIVE_FIELDS)
