from fileinput import filename
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
from planning_agent import PlanningAgent

# Initialize Rich Console for UI
console = Console()
load_dotenv()

class EVSmartFactoryAgent:
    """
    [Coordinator]
    Orchestrates the workflow:
    Planner -> LogRetriever/CSV -> Final Synthesis
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in .env")
            sys.exit(1)

        # Initialize Google GenAI Client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-flash-preview"

        # Initialize Context Storage For Last Retrieval
        self.last_log_context = "No logs retrieved yet."
        self.last_csv_context = "No CSV context yet."

        # Load Data Sources
        self.dfs = {}
        self.data_summary = ""
        self.full_context_csv = ""
        self.log_context = ""

        # Initialize Planning Agent
        print("🧠 Initializing Planning Agent...")
        self.planner = PlanningAgent()

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
            # path = os.path.join("data", path.split("/data/")[-1])  # Ensure path is relative to data directory
            if os.path.exists(path):
                self.dfs[name] = pd.read_csv(path)

            if not os.path.exists(path):
                console.print(f"[bold red]Error:[/bold red] File not found: {path}")
                console.print("Did you run 'python generate_data.py' first?")
                sys.exit(1)

    def get_structured_context(self) -> str:
            if not self.dfs: return "No CSV Data."
            self.data_summary = "--- STRUCTURED DATA (Statistics) ---\n"
            self.full_context_csv = "" # Reset
            for name, df in self.dfs.items():
                # Build Schema Summary
                self.data_summary += f"\nDataset: {name}\nColumns: {', '.join(df.columns)}\nPreview:\n{df.head(3).to_markdown(index=False)}\n"
                # Context Injection
                self.full_context_csv += f"\n=== {name} Data Table ===\n{df.to_csv(index=False)}\n"

            console.print(f"[green]✔ Loaded {len(self.dfs)} datasets[/green]")

    def ask(self, question):
        """
        The main entry point for the Agent.
        1. Plans the query using Planning Agent.
        2. Retrieves relevant logs (RAG) if available.
        3. Prepares structured data context (CSV).
        4. Sends everything to Gemini for reasoning.
        """

        # === Phase 1: Planning (Delegated to Planning Agent) ===
        plan = self.planner.plan_query(question)
        self.last_plan = plan # Save for UI

        action = plan.get("action", "BOTH")
        reason = plan.get("reason", "This query is not related to factory analytics.")

        # === [Planning Guardrail] ===
        if action == "OUT_OF_SCOPE":
            refusal_text = (
                f"🛡️ **Out of Scope**\n\n"
                f"**Reason:** {reason}\n\n"
                f"I am a specialized **EV Factory AI Assistant**. "
                f"I can only help you with:\n"
                f"- 📊 Production Statistics (Yield, SoH)\n"
                f"- 📝 Error Log Analysis (E-301, V2.1.0)\n"
                f"- 🏭 Manufacturing Quality Issues"
            )

            # Create a generator that conforms to the Streamlit stream format.
            # This way, the `for chunk in response_stream` loop in `app.py` will also work correctly.
            class GenericStreamResponse:
                def __init__(self, text):
                    self.text = text

            # Use yield to postback to simulate a streaming effect.
            yield GenericStreamResponse(refusal_text)
            return

        # === Phase 2: Execution (Retrieval) ===
        self.csv_context = ""
        self.log_context = ""

        if action in ["CSV_ONLY", "BOTH"]:
            self.get_structured_context()

        if action in ["LOGS_ONLY", "BOTH"]:
            if self.log_retriever:
                print(f"🔍 RAG Agent is searching logs for: {question}")
                self.log_context = self.log_retriever.get_relevant_logs(question)
                print(f"📄 [DEBUG] Retrieved Log Content: {self.log_context[:200]}...")
            else:
                self.log_context = "Log analysis subsystem is unavailable."

        self.last_csv_context = self.full_context_csv if self.full_context_csv else "Skipped by Planner"
        self.last_log_context = self.log_context if self.log_context else "Skipped by Planner"

        # === Phase 3: Synthesis (Final Answer) ===
        # Construct the Hybrid System Prompt
        self.system_instruction = f"""
        You are the Chief Engineer and Data Strategist of an EV Smart Factory.

        PLANNING DECISION: {action}
        REASONING: {reason}

        Data Schema Preview:
        {self.data_summary}

        YOUR MISSION:
        1. Analyze cross-table correlations (e.g., specific Firmware vs. Quality Issues).
        2. Provide data-driven insights using professional engineering terminology (Yield Rate, SoH, Root Cause).
        3. If the user asks broadly, summarize key risks found in the data.

        Reference Data for your analysis:
        {self.full_context_csv}

        Additionally, you have access to recent production logs from the factory's End-of-Line test station.
        {self.log_context}

        --- INSTRUCTIONS ---
        - **Word Limit:** Keep your answer within 300 words.
        - **General Trends:** If the user asks about stats (e.g., "Yield rate"), rely on CSV data.
        - **Issue Severity:** If the user asks about failures or errors, use green/red highlighting to indicate severity.
        - **Root Causes:** If the user asks about specific failures (e.g., "Why did v2.1.0 fail?"), rely on the LOG entries.
        - **Correlation:** Try to link CSV anomalies (e.g., Low SOH) with Log errors (e.g., Voltage drift).
        - **Actionable Advice:** When identifying a log error, cite the specific Error Code and the Assigned Team.

        """

        # --- [Gemini Model Reasoning Optimization] Content generation parameters ---
        console.print(f"[dim]Initializing {self.model_name} model...[/dim]")

        """
        Sends a message to the model with Exponential Backoff Retry logic.
        """
        max_retries = 3
        wait_time = 2

        for attempt in range(max_retries):
            try:
                # The new API uses generate_content with the stream=True flag
                # response_stream = model.generate_content(question, stream=True)
                # return response_stream

                response = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=self.system_instruction,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.95,
                        top_k=64,
                        max_output_tokens=2048
                    )
                )
                for chunk in response:
                    yield chunk
                return

            except Exception as e:
                # error_msg = str(e).lower()
                # if "429" in error_msg or "quota" in error_msg or "resource_exhausted" in error_msg:
                #     console.print(f"\n[yellow]API Quota Limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})[/yellow]")
                #     time.sleep(wait_time)
                #     wait_time *= 2
                # else:
                #     console.print(f"[bold red]API Error:[/bold red] {e}")
                #     return None

                print(f"Error generating response: {e}")

                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    wait_time *= 2
                    continue
                else:
                    class ErrorChunk:
                        text = f"\n⚠️ Error: {e}"
                    yield ErrorChunk()
                return

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
                console.print("\n[bold dark_slate_gray2]Reporting AI Agent >[/bold dark_slate_gray2]")

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