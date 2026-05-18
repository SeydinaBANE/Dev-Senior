import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt
from agents.biz_manager.agent import agent

app = typer.Typer()
console = Console()


async def chat_loop() -> None:
    console.print("[bold blue]Business Manager[/] — prêt. Tape 'exit' pour quitter.\n")
    history: list = []

    async with agent.run_mcp_servers():
        while True:
            user_input = Prompt.ask("[bold cyan]Toi[/]")
            if user_input.lower() in ("exit", "quit"):
                break

            with console.status("Réflexion..."):
                result = await agent.run(user_input, message_history=history)

            console.print(f"\n[bold blue]Business Manager[/]\n{result.data}\n")
            history = result.all_messages()


@app.command()
def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    app()
