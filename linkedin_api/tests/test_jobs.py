from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestSearchJobs:
    def test_search_jobs_returns_job_list(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(
                return_value=httpx.Response(200, json={})
            )
            rsps.get("/voyager/api/jobs/jobSearch").mock(
                return_value=httpx.Response(200, json={
                    "data": {
                        "elements": [
                            {
                                "title": "Software Engineer",
                                "company": {"name": "TechCorp"},
                                "location": "San Francisco, CA"
                            },
                            {
                                "title": "Senior Developer",
                                "company": {"name": "StartupCo"},
                                "location": "Austin, TX"
                            }
                        ]
                    }
                })
            )
            from linkedin_api.capabilities.jobs import search_jobs
            results = search_jobs("software engineer", location="California", vault=vault)
            assert len(results) == 2
            assert results[0]["title"] == "Software Engineer"
            assert results[0]["company"] == "TechCorp"
            assert results[0]["location"] == "San Francisco, CA"
        client.close()

    def test_search_jobs_raises_on_401(self, vault):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(401))
            from linkedin_api.capabilities.jobs import search_jobs
            with pytest.raises(SessionExpiredError):
                search_jobs("engineer", location=None, vault=vault)
        client.close()


class TestBookmarkJob:
    def test_bookmark_job_returns_success_on_200(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(
                return_value=httpx.Response(200, json={})
            )
            rsps.put("/voyager/api/jobs/jobSearch/12345/bookmark").mock(
                return_value=httpx.Response(200)
            )
            from linkedin_api.capabilities.jobs import bookmark_job
            result = bookmark_job("12345", vault=vault)
            assert result["success"] is True
        client.close()

    def test_bookmark_job_returns_success_on_201(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(
                return_value=httpx.Response(200, json={})
            )
            rsps.put("/voyager/api/jobs/jobSearch/12345/bookmark").mock(
                return_value=httpx.Response(201)
            )
            from linkedin_api.capabilities.jobs import bookmark_job
            result = bookmark_job("12345", vault=vault)
            assert result["success"] is True
        client.close()

    def test_bookmark_job_raises_on_401(self, vault):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(401))
            from linkedin_api.capabilities.jobs import bookmark_job
            with pytest.raises(SessionExpiredError):
                bookmark_job("12345", vault=vault)
        client.close()