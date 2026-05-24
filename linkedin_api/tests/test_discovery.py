from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestSearchPeople:
    def test_search_people_returns_list(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.get("/voyager/api/search/blended").mock(
            return_value=httpx.Response(200, json={
                "data": {
                    "elements": [
                        {
                            "person": {
                                "fullName": "Jane Smith",
                                "headline": "Software Engineer",
                                "entityUrn": "urn:li:member:123456"
                            }
                        }
                    ]
                }
            })
        )
        from linkedin_api.capabilities.discovery import search_people
        results = search_people("software engineer", limit=5, client=client, vault=vault)
        assert len(results) == 1
        assert results[0]["name"] == "Jane Smith"
        assert results[0]["headline"] == "Software Engineer"
        assert "linkedin.com/in/123456" in results[0]["profile_url"]
        client.close()

    def test_search_people_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.discovery import search_people
        with pytest.raises(SessionExpiredError):
            search_people("engineer", limit=5, client=client, vault=vault)
        client.close()


class TestGetProfile:
    def test_get_profile_by_urn(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.get("/voyager/api/profile/123456").mock(
            return_value=httpx.Response(200, json={
                "headline": "Senior Developer at TechCorp",
                "about": "Passionate about building great software.",
                "positions": {
                    "elements": [
                        {
                            "title": "Senior Developer",
                            "companyName": "TechCorp",
                            "locationName": "San Francisco"
                        }
                    ]
                },
                "education": {
                    "elements": [
                        {"schoolName": "MIT", "degreeName": "BS Computer Science"}
                    ]
                }
            })
        )
        from linkedin_api.capabilities.discovery import get_profile
        result = get_profile("urn:li:member:123456", client=client, vault=vault)
        assert result["headline"] == "Senior Developer at TechCorp"
        assert result["about"] == "Passionate about building great software."
        assert len(result["experience"]) == 1
        assert len(result["education"]) == 1
        client.close()

    def test_get_profile_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.discovery import get_profile
        with pytest.raises(SessionExpiredError):
            get_profile("urn:li:member:123456", client=client, vault=vault)
        client.close()