from google.adk.agents import Agent
from CustomerServiceAgent.orchestrator import orchestrator

def handle_complaint_tool(complaint_text: str) -> dict:
    """Handle a customer complaint through the ResolveX pipeline."""
    return orchestrator.handle_complaint(complaint_text)

root_agent = Agent(
    name="CustomerServiceAgent",
    model="gemini-2.5-flash",
    description="ResolveX Customer Service Agent that handles product complaints end-to-end.",
    instruction="""You are a customer service agent for ResolveX. 
    When a customer submits a complaint, use the handle_complaint_tool to process it.
    Always be polite, empathetic, and professional.
    After processing, summarize the resolution and complaint ID for the customer.""",
    tools=[handle_complaint_tool],
)
