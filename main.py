import sys
from rich.console import Console
from rich.panel import Panel
from rag_agent import EVSmartFactoryAgent

# Initialize Rich Console (for pretty output)
console = Console()

def main():
    # 1. Display the startup banner
    console.print(Panel("[bold yellow]Initializing Giga's EV Factory Agent...[/bold yellow]", border_style="yellow"))

    try:
        # 2. Initialize the Agent
        agent = EVSmartFactoryAgent()
        console.print("[green]✔ Agent System Ready.[/green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to initialize Agent:[/bold red] {e}")
        console.print("[dim]Hint: Check your .env file or API Key.[/dim]")
        return

    # 3. Display the welcome interface
    console.print(Panel.fit(
        "[bold cyan]EV Smart Factory Analytics System (CLI Mode)[/bold cyan]\n"
        "[dim]Architecture: Planner -> RAG -> Gemini 2.0/3.0[/dim]\n\n"
        "Type 'exit' or 'quit' to end session.",
        border_style="blue"
    ))

    # 4. Main conversation loop
    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold green]Chief Engineer > [/bold green]")

            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Shutting down...[/yellow]")
                break

            if not user_input.strip():
                continue

            # 5. Display thinking animation (Simulating Agent processing)
            with console.status("[bold blue]Agent is planning & retrieving...[/bold blue]", spinner="dots"):
                # Call the Agent's ask method (Triggers Planning -> RAG -> Synthesis)
                response_stream = agent.ask(user_input)

            # 6. Stream the output results
            console.print("\n[bold purple]AI Agent >[/bold purple]")

            full_response = ""

            if response_stream:
                for chunk in response_stream:
                    # [Compatibility Handling]
                    # Supports native Gemini chunks (chunk.text)
                    # as well as our custom GenericStreamResponse (chunk.text)
                    if hasattr(chunk, 'text') and chunk.text:
                        text = chunk.text
                        print(text, end="", flush=True)
                        full_response += text
                print("\n") # Print a newline at the end

            # (Optional) Display debug information about the planning decision
            # This helps you understand why the agent chose a specific action (e.g., LOGS_ONLY)
            if hasattr(agent, 'last_plan') and agent.last_plan:
                 action = agent.last_plan.get('action')
                 reason = agent.last_plan.get('reason')
                 console.print(f"[dim]🔍 Plan: {action} | Reason: {reason}[/dim]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    main()