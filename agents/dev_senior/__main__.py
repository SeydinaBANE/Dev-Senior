import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt
from agents.dev_senior.agent import agent

app = typer.Typer()
console = Console()


async def chat_loop() -> None:
    console.print("[bold green]Dev Senior[/] — prêt. Tape 'exit' pour quitter.\n")
    history: list[dict[str, str]] = []

    while True:
        user_input = Prompt.ask("[bold cyan]Toi[/]")
        if user_input.lower() in ("exit", "quit"):
            break

        with console.status("Réflexion..."):
            result = await agent.run(user_input, message_history=history)

        console.print(f"\n[bold green]Dev Senior[/]\n{result.data}\n")
        history = result.all_messages()


@app.command()
def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    app()
