from google.adk.agents import Agent
from .orchestrator import orchestrator

def handle_customer_complaint(complaint: str) -> dict:
    return orchestrator.handle_complaint(complaint)

root_agent = Agent(
    name="CustomerServiceAgent",
    model="gemini-2.5-flash",
    description="Autonomous customer complaint resolution agent.",
    instruction=(
        "You help resolve customer complaints. "
        "When the user provides a complaint, use the complaint handling tool."
    ),
    tools=[handle_customer_complaint],
)
