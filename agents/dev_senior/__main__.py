import asyncio
from typing import Any

import typer
from rich.console import Console
from rich.prompt import Prompt

from agents.dev_senior.agent import agent
from memory.dev_senior.retriever import retrieve_context
from observability.langfuse_config import configure_observability, get_langfuse

app = typer.Typer()
console = Console()


async def chat_loop() -> None:
    configure_observability("dev-senior")
    console.print("[bold green]Dev Senior[/] — prêt. Tape 'exit' pour quitter.\n")
    history: list[Any] = []

    async with agent.run_mcp_servers():
        while True:
            user_input = Prompt.ask("[bold cyan]Toi[/]")
            if user_input.lower() in ("exit", "quit"):
                break

            context = retrieve_context(user_input)
            prompt = f"{context}\n\n{user_input}" if context else user_input

            lf = get_langfuse()
            trace = (
                lf.trace(
                    name="dev-senior-chat",
                    input={"message": user_input},
                    metadata={"agent": "dev-senior", "mode": "cli"},
                )
                if lf
                else None
            )

            with console.status("Réflexion..."):
                result = await agent.run(prompt, message_history=history)

            response = result.output
            if trace:
                try:
                    trace.update(output={"response": response})
                except Exception:
                    pass

            console.print(f"\n[bold green]Dev Senior[/]\n{response}\n")
            history = result.all_messages()

    if lf := get_langfuse():
        try:
            lf.flush()
        except Exception:
            pass


@app.command()
def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    app()
