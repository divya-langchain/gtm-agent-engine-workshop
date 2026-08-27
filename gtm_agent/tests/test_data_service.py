import unittest
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")
from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile


class UpdateProspectInfoTest(unittest.TestCase):
    def test_update_persists_source_and_cached_tech_stack(self):
        prospect_id = "LEAD-39002"
        technology = "Terraform"
        record = data_service.get_prospect_record(prospect_id)
        original_stack = list(record["tech_stack"])
        cached_profile = {"prospect_id": prospect_id, "tech_stack": list(original_stack)}
        data_service.save_profile_to_db(prospect_id, cached_profile)

        try:
            result = data_service.update_prospect_info(prospect_id, technology)

            self.assertTrue(result["updated"])
            self.assertIn(technology, data_service.get_prospect_record(prospect_id)["tech_stack"])
            self.assertIn(technology, data_service.fetch_tech_stack(prospect_id))
            profile = build_prospect_profile.invoke({"prospect_id": prospect_id})
            self.assertIn(technology, profile["prospect_profile"]["tech_stack"])
        finally:
            record["tech_stack"] = original_stack
            data_service._PROFILES.pop(prospect_id, None)


if __name__ == "__main__":
    unittest.main()
