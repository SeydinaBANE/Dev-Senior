import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt

from observability.langfuse_config import configure_observability, get_langfuse
from memory.biz_manager.context import retrieve_context, save_interaction
from agents.biz_manager.agent import agent

app = typer.Typer()
console = Console()


async def chat_loop() -> None:
    configure_observability("biz-manager")
    console.print("[bold blue]Business Manager[/] — prêt. Tape 'exit' pour quitter.\n")
    history: list = []

    async with agent.run_mcp_servers():
        while True:
            user_input = Prompt.ask("[bold cyan]Toi[/]")
            if user_input.lower() in ("exit", "quit"):
                break

            context = retrieve_context(user_input)
            prompt = f"{context}\n\n{user_input}" if context else user_input

            lf = get_langfuse()
            trace = lf.trace(
                name="biz-manager-chat",
                input={"message": user_input},
                metadata={"agent": "biz-manager", "mode": "cli"},
            ) if lf else None

            with console.status("Réflexion..."):
                result = await agent.run(prompt, message_history=history)

            response = result.data
            if trace:
                try:
                    trace.update(output={"response": response})
                except Exception:
                    pass

            console.print(f"\n[bold blue]Business Manager[/]\n{response}\n")
            history = result.all_messages()
            save_interaction(user_input, response)

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
