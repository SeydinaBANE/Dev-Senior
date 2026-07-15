"""
Adapter HubSpot — appels HTTP bruts vers l'API HubSpot. mcp_servers/crm/server.py
garde les guard-clauses (CRM_API_KEY) et le formatage de réponse pour le LLM.
"""

import httpx

HUBSPOT_BASE = "https://api.hubapi.com"


class HubSpotClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def search_contacts(self, query: str) -> list[dict]:
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "CONTAINS_TOKEN", "value": query}
                    ]
                }
            ],
            "properties": ["firstname", "lastname", "email", "company", "phone"],
            "limit": 20,
        }
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("results", [])

    def get_contact(self, contact_id: str) -> dict:
        props = "firstname,lastname,email,company,phone,lifecyclestage,notes_last_updated"
        r = httpx.get(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}?properties={props}",
            headers=self._headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()["properties"]

    def create_contact(self, email: str, firstname: str, lastname: str, company: str) -> str:
        payload = {
            "properties": {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "company": company,
            }
        }
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()["id"]

    def list_deals(self, stage: str) -> list[dict]:
        payload: dict = {
            "properties": ["dealname", "amount", "dealstage", "closedate"],
            "limit": 30,
        }
        if stage:
            payload["filterGroups"] = [
                {"filters": [{"propertyName": "dealstage", "operator": "EQ", "value": stage}]}
            ]
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/deals/search",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("results", [])

    def create_note(self, contact_id: str, note: str) -> None:
        payload = {
            "properties": {"hs_note_body": note, "hs_timestamp": "now"},
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
                }
            ],
        }
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/notes",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        r.raise_for_status()
