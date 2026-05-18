"""
MCP Server CRM — à adapter selon le CRM utilisé.

Structure prête pour brancher : HubSpot, Notion, Airtable, ou API interne.
Configurer CRM_TYPE et CRM_API_KEY dans .env.

Outils exposés :
- search_contacts  : chercher un contact
- get_contact      : détail d'un contact
- create_contact   : créer un contact
- list_deals       : lister les opportunités
- create_note      : ajouter une note sur un contact
"""
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("crm")

CRM_TYPE = os.getenv("CRM_TYPE", "hubspot")  # hubspot | notion | airtable | custom
CRM_API_KEY = os.getenv("CRM_API_KEY", "")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "")

HUBSPOT_BASE = "https://api.hubapi.com"


def _hubspot_headers() -> dict:
    return {"Authorization": f"Bearer {CRM_API_KEY}", "Content-Type": "application/json"}


# ── HubSpot ───────────────────────────────────────────────────────────────────

@mcp.tool()
def search_contacts(query: str) -> str:
    """Recherche des contacts dans le CRM.

    Args:
        query: Nom, email ou entreprise à chercher.
    """
    if not CRM_API_KEY:
        return "CRM_API_KEY manquant dans .env"
    try:
        payload = {
            "filterGroups": [{
                "filters": [{"propertyName": "email", "operator": "CONTAINS_TOKEN", "value": query}]
            }],
            "properties": ["firstname", "lastname", "email", "company", "phone"],
            "limit": 20,
        }
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
            json=payload,
            headers=_hubspot_headers(),
            timeout=10,
        )
        r.raise_for_status()
        contacts = r.json().get("results", [])
        if not contacts:
            return f"Aucun contact trouvé pour '{query}'."
        lines = []
        for c in contacts:
            p = c["properties"]
            lines.append(
                f"[{c['id']}] {p.get('firstname', '')} {p.get('lastname', '')} "
                f"<{p.get('email', '')}> — {p.get('company', '')}"
            )
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"Erreur CRM : {e}"


@mcp.tool()
def get_contact(contact_id: str) -> str:
    """Retourne les détails d'un contact CRM.

    Args:
        contact_id: ID du contact (visible dans search_contacts).
    """
    if not CRM_API_KEY:
        return "CRM_API_KEY manquant dans .env"
    try:
        props = "firstname,lastname,email,company,phone,lifecyclestage,notes_last_updated"
        r = httpx.get(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}?properties={props}",
            headers=_hubspot_headers(),
            timeout=10,
        )
        r.raise_for_status()
        p = r.json()["properties"]
        return "\n".join(f"{k}: {v}" for k, v in p.items() if v)
    except httpx.HTTPError as e:
        return f"Erreur CRM : {e}"


@mcp.tool()
def create_contact(email: str, firstname: str = "", lastname: str = "", company: str = "") -> str:
    """Crée un contact dans le CRM.

    Args:
        email:     Email du contact (obligatoire).
        firstname: Prénom.
        lastname:  Nom.
        company:   Entreprise.
    """
    if not CRM_API_KEY:
        return "CRM_API_KEY manquant dans .env"
    try:
        payload = {"properties": {"email": email, "firstname": firstname, "lastname": lastname, "company": company}}
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
            json=payload,
            headers=_hubspot_headers(),
            timeout=10,
        )
        r.raise_for_status()
        contact_id = r.json()["id"]
        return f"Contact créé : ID {contact_id}"
    except httpx.HTTPError as e:
        return f"Erreur CRM : {e}"


@mcp.tool()
def list_deals(stage: str = "") -> str:
    """Liste les opportunités commerciales.

    Args:
        stage: Filtre par étape (ex: 'appointmentscheduled', 'closedwon'). Vide = tout.
    """
    if not CRM_API_KEY:
        return "CRM_API_KEY manquant dans .env"
    try:
        payload: dict = {
            "properties": ["dealname", "amount", "dealstage", "closedate"],
            "limit": 30,
        }
        if stage:
            payload["filterGroups"] = [{
                "filters": [{"propertyName": "dealstage", "operator": "EQ", "value": stage}]
            }]
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/deals/search",
            json=payload,
            headers=_hubspot_headers(),
            timeout=10,
        )
        r.raise_for_status()
        deals = r.json().get("results", [])
        if not deals:
            return "Aucune opportunité trouvée."
        lines = []
        for d in deals:
            p = d["properties"]
            lines.append(
                f"[{d['id']}] {p.get('dealname', '')} — "
                f"{p.get('amount', '?')}€ | {p.get('dealstage', '')} | clôture: {p.get('closedate', '')[:10]}"
            )
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"Erreur CRM : {e}"


@mcp.tool()
def create_note(contact_id: str, note: str) -> str:
    """Ajoute une note sur un contact dans le CRM.

    Args:
        contact_id: ID du contact HubSpot.
        note:       Contenu de la note.
    """
    if not CRM_API_KEY:
        return "CRM_API_KEY manquant dans .env"
    try:
        payload = {
            "properties": {"hs_note_body": note, "hs_timestamp": "now"},
            "associations": [{"to": {"id": contact_id}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]}],
        }
        r = httpx.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/notes",
            json=payload,
            headers=_hubspot_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return f"Note ajoutée sur le contact {contact_id}."
    except httpx.HTTPError as e:
        return f"Erreur CRM : {e}"


if __name__ == "__main__":
    mcp.run()
