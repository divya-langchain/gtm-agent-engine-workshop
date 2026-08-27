import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import (
    SENSITIVE_PROSPECT_FIELDS,
    build_prospect_profile,
    data_service,
    get_prospect,
)


class SensitiveProspectFieldsTest(unittest.TestCase):
    def test_prospect_tools_exclude_sensitive_fields(self):
        data_service._PROFILES.clear()

        results = [
            get_prospect.invoke({"prospect_id": "LEAD-39002"})["prospect"],
            build_prospect_profile.invoke({"prospect_id": "LEAD-39002"})[
                "prospect_profile"
            ],
        ]

        for result in results:
            serialized = json.dumps(result)
            self.assertTrue(SENSITIVE_PROSPECT_FIELDS.isdisjoint(result))
            self.assertIsNone(re.search(r"\b\d{3}-\d{2}-\d{4}\b", serialized))
            self.assertIsNone(re.search(r"\b\d{16}\b", serialized))


if __name__ == "__main__":
    unittest.main()
