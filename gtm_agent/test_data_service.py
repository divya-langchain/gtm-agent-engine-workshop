import os
import sys
import unittest
from pathlib import Path

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["OPENAI_API_KEY"] = "test-key"

repo_dir = Path(__file__).resolve().parent
sys.path = [path for path in sys.path if Path(path or ".").resolve() != repo_dir]
sys.path.insert(0, str(repo_dir.parent))

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile


class UpdateProspectInfoTest(unittest.TestCase):
    def setUp(self):
        self.original_tech_stack = list(data_service.PROSPECTS["LEAD-71001"]["tech_stack"])
        data_service._PROFILES.clear()
        data_service.PROSPECTS["LEAD-71001"]["tech_stack"] = [
            technology
            for technology in self.original_tech_stack
            if technology != "Kafka"
        ]

    def tearDown(self):
        data_service.PROSPECTS["LEAD-71001"]["tech_stack"] = self.original_tech_stack
        data_service._PROFILES.clear()

    def test_update_persists_and_invalidates_profile_cache(self):
        profile_before_update = build_prospect_profile.invoke({"prospect_id": "LEAD-71001"})

        result = data_service.update_prospect_info("LEAD-71001", "Kafka")

        self.assertTrue(result["updated"])
        self.assertIn("Kafka", data_service.fetch_tech_stack("LEAD-71001"))
        profile_after_update = build_prospect_profile.invoke({"prospect_id": "LEAD-71001"})
        self.assertNotEqual(profile_before_update["prospect_profile"], profile_after_update["prospect_profile"])
        self.assertIn("Kafka", profile_after_update["prospect_profile"]["tech_stack"])


if __name__ == "__main__":
    unittest.main()
