import os
import sys
import time
import random
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich import print
from log_analyzer import LogRetriever

# Initialize Rich Console for UI
console = Console()
load_dotenv()

class EVSmartFactoryAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in .env")
            sys.exit(1)

        # Initialize Google GenAI Client
        # Using the experimental flash model for low latency
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-flash-preview"

        # Initialize Context Storage For Last Retrieval
        self.last_log_context = "No logs retrieved yet."
        self.last_csv_context = "No CSV context yet."

        # Load Structured Data Sources
        self.dfs = {}
        self.data_summary = ""
        self.full_context_csv = ""

        # Initialize Unstructured Data Retriever (Logs)
        print("🚀 Initializing Log Analysis Subsystem (RAG)...")
        try:
            # Read the data/logs folder and build a vector index.
            self.log_retriever = LogRetriever()
            print("✅ Log Subsystem Ready.")
        except Exception as e:
            print(f"⚠️ Warning: Log system failed to initialize: {e}")
            self.log_retriever = None

        # Load data on initialization
        self.load_data()

    def load_data(self):
        # Load Data Sources into Pandas DataFrames
        self.data_files = {
            "Manufacturing": "data/factory_manufacturing.csv",
            "Performance": "data/vehicle_performance.csv",
            "Issues": "data/quality_issues.csv"
        }

        console.print("[dim]Loading datasets...[/dim]")
        for name, path in self.data_files.items():
            if not os.path.exists(path):
                console.print(f"[bold red]Error:[/bold red] File not found: {path}")
                console.print("Did you run 'python generate_data.py' first?")
                sys.exit(1)

            df = pd.read_csv(path)
            self.dfs[name] = df

            # Build Schema Summary
            self.data_summary += f"\nDataset: {name}\nColumns: {', '.join(df.columns)}\nPreview:\n{df.head(3).to_markdown(index=False)}\n"

            # Context Injection
            self.full_context_csv += f"\n=== {name} Data Table ===\n{df.to_csv(index=False)}\n"
            console.print(f"[green]✔ Loaded {name}: {len(df)} rows[/green]")

    def ask(self, question):
        """
        The main entry point for the Agent.
        1. Retrieves relevant logs (RAG) if available.
        2. Prepares structured data context (CSV).
        3. Sends everything to Gemini for reasoning.
        """

        # Step 1: Get Context from CSVs (The original logic)
        self.last_csv_context = self.full_context_csv # Store last CSV context for debugging

        # Step 2: Get Context from Logs (RAG Retrieval)
        log_context = LogRetriever(log_dir="data/logs")
        if self.log_retriever:
            print(f"🔍 RAG Agent is searching logs for: {question}")
            log_context = self.log_retriever.get_relevant_logs(question)
            print(f"📄 [DEBUG] Retrieved Log Content: {log_context[:200]}...")
        else:
            log_context = "Log analysis subsystem is unavailable."

        self.last_log_context = log_context # Store last log retrieval for debugging

        # Step 3: Construct the Hybrid System Prompt
        # We combine insights from both CSV (Trends) and Logs (Root Causes)
        self.system_instruction = f"""
        You are the Chief Engineer and Data Strategist of an EV Smart Factory.
        You have access to 3 interconnected datasets:
        1. Manufacturing: Production logs (Labor, Status, Line ID).
        2. Performance: Vehicle telemetry (Battery SoH, Firmware Version, Sensor Score).
        3. Issues: Quality tickets and defects.

        Data Schema Preview:
        {self.data_summary}

        YOUR MISSION:
        1. Analyze cross-table correlations (e.g., specific Firmware vs. Quality Issues).
        2. Provide data-driven insights using professional engineering terminology (Yield Rate, SoH, Root Cause).
        3. If the user asks broadly, summarize key risks found in the data.

        Reference Data for your analysis:
        {self.full_context_csv}

        Additionally, you have access to recent production logs from the factory's End-of-Line test station.
        {log_context}

        --- INSTRUCTIONS ---
        - **General Trends:** If the user asks about stats (e.g., "Yield rate"), rely on CSV data.
        - **Root Causes:** If the user asks about specific failures (e.g., "Why did v2.1.0 fail?"), rely on the LOG entries.
        - **Correlation:** Try to link CSV anomalies (e.g., Low SOH) with Log errors (e.g., Voltage drift).
        - **Actionable Advice:** When identifying a log error, cite the specific Error Code and the Assigned Team.

        """

        # --- MODEL UPDATE: Gemini 3 Flash Preview ---
        console.print("[dim]Initializing Gemini 3 Flash Preview model...[/dim]")
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7,
                top_p=0.95,
                top_k=64,
                max_output_tokens=8192,
            )
        )

        """
        Sends a message to the model with Exponential Backoff Retry logic.
        """
        max_retries = 3
        wait_time = 2

        for attempt in range(max_retries):
            try:
                response_stream = self.chat.send_message_stream(question)
                return response_stream

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "quota" in error_msg or "resource_exhausted" in error_msg:
                    console.print(f"\n[yellow]API Quota Limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})[/yellow]")
                    time.sleep(wait_time)
                    wait_time *= 2
                else:
                    console.print(f"[bold red]API Error:[/bold red] {e}")
                    return None

        console.print("[bold red]Failed after multiple retries. Please check your API quota plan.[/bold red]")
        return None

def main():
    agent = EVSmartFactoryAgent()

    # Define a custom color for font in Rich
    OWNER_COLOR = "#DBCA06"
    DB_COLOR = "#cd7407"

    # Display a nice welcome interface
    console.print(Panel.fit(
        "[bold cyan]EV Smart Factory Analytics & Reporting System (Agentic RAG)[/bold cyan]\n"
        "[dim]Powered by Gemini 3.0 Flash[/dim]\n\n"
        f"[bold {OWNER_COLOR}]System Owner: Giga Lu[/bold {OWNER_COLOR}]\n\n"
        f"Connected Datasets: [{DB_COLOR}]Manufacturing, Performance, Quality Issues[/{DB_COLOR}]\n\n"
        "Type 'exit' or 'quit' to end session.",
        border_style="blue"
    ))
    console.print("\n[dim]Try asking: 'Analyze if Firmware v2.1.0 is causing battery issues'[/dim]")

    while True:
        try:
            user_input = console.input("\n[bold green]Chief Engineer > [/bold green]")

            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Shutting down Agentic RAG Reporting Systems... See you next time![/yellow]")
                break

            if not user_input.strip():
                continue

            # === Agentic Thought Process Animation ===
            # Define the backend task steps that the Agent may execute.
            thought_steps = [
                "Authenticating with Secure Data Lake...",
                "Retrieving Manufacturing Schemas...",
                "Querying Vehicle Telemetry DB...",
                "Cross-referencing Quality Tickets...",
                "Running Correlation Analysis...",
                "Detecting Anomalies in Sensor Data...",
                "Calculating Yield Rates...",
                "Optimizing Response Vector..."
            ]

            response_stream = None
            first_chunk = None

            # Use the 'earth' spinner to simulate the feeling of operating a global factory.
            with console.status("[bold blue]Initializing Agent...[/bold blue]", spinner="earth") as status:

                # Randomly select 2-4 steps to simulate the thinking process.
                selected_steps = random.sample(thought_steps, random.randint(3, 5))

                for step in selected_steps:
                    # Simulate the processing time for each step (0.3 ~ 0.8 seconds).
                    time.sleep(random.uniform(0.3, 0.8))
                    status.update(f"[bold cyan]{step}[/bold cyan]")

                # Finally, it shows that a response is being generated.
                status.update("[bold green]Finalizing Insights with Gemini...[/bold green]")

                # Call API
                response_stream = agent.ask(user_input)

                # Capture the first chunk to end the spinner.
                if response_stream:
                    status.update("[bold green]Synthesizing Answer...[/bold green]")
                    try:
                        # next() will force the program to wait until the first token is returned.
                        # During this time, the spinner will still be spinning!
                        first_chunk = next(response_stream)
                    except StopIteration:
                        pass
                    except Exception as e:
                        pass

            # === Stream Output ===
            if response_stream and first_chunk:
                console.print("\n[bold purple]AI Assistant >[/bold purple]")

                # A. Print the first chunk
                if first_chunk.text:
                    print(first_chunk.text, end="", flush=True)

                # B. Stream the rest of the response
                for chunk in response_stream:
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                print("\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Unexpected Error:[/red] {e}")
            break

if __name__ == "__main__":
    main()