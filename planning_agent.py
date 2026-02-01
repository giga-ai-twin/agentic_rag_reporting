import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class PlanningAgent:
    """
    [Planning Agent]
    Responsibilities:
    1. Intent Recognition: Understands what the user wants.
    2. Semantic Routing: Decides which tool (CSV or Logs) is best suited.
    3. Error Handling: Falls back to a safe strategy if unsure.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found via dotenv.")

        # Initialize its own Gemini Client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-flash-preview"

    def plan_query(self, query: str) -> dict:
        """
        Analyzes the user query and returns a structured plan (JSON).
        """
        print(f"🧠 [Planning Agent] Analyzing intent for: {query}")

        planning_prompt = f"""
        You are the Planning Agent for a Smart Factory System.
        Your job is to route the user's query to the correct data source.

        AVAILABLE DATA SOURCES:
        1. **CSV_Database**: Contains numerical stats, yield rates, battery SoH averages, production counts.
        2. **Log_System**: Contains specific error codes (e.g., E-301), root cause details, text descriptions of failures, specific VIN events.

        INSTRUCTIONS:
        - Analyze the User Query.
        - Output a strictly valid JSON object with 'action' and 'reason'.
        - 'action' must be one of: ["CSV_ONLY", "LOGS_ONLY", "BOTH", "OUT_OF_SCOPE"].

        RULES FOR DECISION:
        - If asking for averages, counts, trends, or overall stats -> "CSV_ONLY"
        - If asking for specific error details, "why" something failed, or specific ID events -> "LOGS_ONLY"
        - If asking for complex diagnosis (e.g., "Why is yield low?") connecting stats to causes -> "BOTH"
        - If asking about weather, coding help, joke, or non-factory topics -> "OUT_OF_SCOPE"

        User Query: "{query}"

        JSON Output:
        """

        try:
            # Generate JSON response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=planning_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )

            plan = json.loads(response.text)
            print(f"📋 [Planning Agent] Decision: {plan.get('action')}")
            return plan

        except Exception as e:
            print(f"⚠️ [Planning Agent] Error: {e}. Defaulting to BOTH.")
            return {"action": "BOTH", "reason": "Planner error fallback."}

# Test block
if __name__ == "__main__":
    planner = PlanningAgent()
    print(planner.plan_query("What is the average yield rate?"))