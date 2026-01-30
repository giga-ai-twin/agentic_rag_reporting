import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Initialize Rich Console (for beautiful output)
console = Console()

class GeminiAssistant:
    def __init__(self):
        self.configure_api()
        self.model = self.setup_model()
        self.chat_session = self.model.start_chat(history=[])

    def configure_api(self):
        """Load environment variables and configure the API"""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            console.print("[bold red]Error:[/bold red] API Key not found. Please check your .env file.")
            sys.exit(1)
        genai.configure(api_key=api_key)

    def setup_model(self):
        """Set up model parameters and System Instruction"""
        # This demonstrates the mindset of Prompt Engineering: giving the AI a role
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
        
        # System Instruction: Define the AI's code of conduct (this is important in an Agentic Workflow)
        system_instruction = (
            "You are a Senior Tech Lead assistant. "
            "Answer questions with concise, architectural-level insights. "
            "Use Markdown formatting for code blocks and lists."
        )

        return genai.GenerativeModel(
            # See the full list of Gemini models here: https://developers.generativeai.google/models
            model_name="gemini-1.5-flash-preview",
            generation_config=generation_config,
            system_instruction=system_instruction
        )

    def send_message(self, message):
        """Send a message and stream the response"""
        try:
            response = self.chat_session.send_message(message, stream=True)
            return response
        except Exception as e:
            console.print(f"[bold red]API Error:[/bold red] {e}")
            return None

def main():
    assistant = GeminiAssistant()
    
    console.print(Panel.fit("[bold cyan]Giga's AI Assistant (Powered by Gemini 3.0)[/bold cyan]\nType 'exit' or 'quit' to end session.", border_style="blue"))

    while True:
        try:
            # Use Rich's input style
            user_input = console.input("[bold green]You > [/bold green]")
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if not user_input.strip():
                continue

            # Show processing status
            with console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
                response_stream = assistant.send_message(user_input)

            # Stream the output (looks more futuristic)
            console.print("\n[bold purple]Gemini >[/bold purple]")
            full_response = ""
            if response_stream:
                for chunk in response_stream:
                    print(chunk.text, end="", flush=True)
                    full_response += chunk.text
                print("\n") # Newline
            
            # (Optional) If you want to re-render Markdown format, you can use the line below, but it's harder to do in real-time in stream mode
            # console.print(Markdown(full_response))
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            break

if __name__ == "__main__":
    main()