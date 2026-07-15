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

from mcp_servers.crm.adapters.hubspot_client import HubSpotClient

mcp = FastMCP("crm")

CRM_TYPE = os.getenv("CRM_TYPE", "hubspot")  # hubspot | notion | airtable | custom
CRM_API_KEY = os.getenv("CRM_API_KEY", "")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "")


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
        contacts = HubSpotClient(CRM_API_KEY).search_contacts(query)
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
        p = HubSpotClient(CRM_API_KEY).get_contact(contact_id)
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
        contact_id = HubSpotClient(CRM_API_KEY).create_contact(email, firstname, lastname, company)
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
        deals = HubSpotClient(CRM_API_KEY).list_deals(stage)
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
        HubSpotClient(CRM_API_KEY).create_note(contact_id, note)
        return f"Note ajoutée sur le contact {contact_id}."
    except httpx.HTTPError as e:
        return f"Erreur CRM : {e}"


if __name__ == "__main__":
    mcp.run()
