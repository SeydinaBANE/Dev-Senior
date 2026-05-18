import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt

from observability.logfire_config import configure_logfire
from memory.biz_manager.context import retrieve_context, save_interaction
from agents.biz_manager.agent import agent

app = typer.Typer()
console = Console()


async def chat_loop() -> None:
    configure_logfire("biz-manager")
    console.print("[bold blue]Business Manager[/] — prêt. Tape 'exit' pour quitter.\n")
    history: list = []

    async with agent.run_mcp_servers():
        while True:
            user_input = Prompt.ask("[bold cyan]Toi[/]")
            if user_input.lower() in ("exit", "quit"):
                break

            # Injection du contexte mémorisé pertinent
            context = retrieve_context(user_input)
            prompt = f"{context}\n\n{user_input}" if context else user_input

            with console.status("Réflexion..."):
                result = await agent.run(prompt, message_history=history)

            response = result.data
            console.print(f"\n[bold blue]Business Manager[/]\n{response}\n")
            history = result.all_messages()

            # Mémorisation de l'interaction pour enrichir le contexte futur
            save_interaction(user_input, response)


@app.command()
def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    app()
