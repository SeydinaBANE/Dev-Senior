"""
Singleton de compatibilité — utilisé par agents/dev_senior/__main__.py (CLI).
Le serveur FastAPI passe par agents.registry.AgentRegistry (app.state.agents).
"""

from agents.adapters.dev_senior_agent import build_agent

agent = build_agent()
