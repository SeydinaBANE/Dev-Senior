"""
Singleton de compatibilité — utilisé par agents/biz_manager/__main__.py (CLI).
Le serveur FastAPI passe par agents.registry.AgentRegistry (app.state.agents).
"""

from agents.adapters.biz_manager_agent import build_agent

agent = build_agent()
