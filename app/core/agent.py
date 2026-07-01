import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from app.core.session import CallSession
from app.core.guardrails import guardrail_layer
from app.config import settings

logger = logging.getLogger("voice_agent.agent")

# =====================================================================
# Bounded Tool Helper Signatures for Gemini Schema Parsing
# =====================================================================

def check_availability(date: str, hall_name: Optional[str] = None) -> str:
    """Check availability of halls on a given date. If hall_name is not provided, 
    returns a list of all available halls on that date.
    
    Args:
        date: The date to check in YYYY-MM-DD format.
        hall_name: Optional name of a specific hall to check (e.g., Main Hall).
    """
    pass

def get_pricing(hall_name: str) -> str:
    """Retrieve pricing details for a given hall.
    
    Args:
        hall_name: The name of the hall to query pricing for (e.g., Main Hall).
    """
    pass

def stage_booking(date: str, hall_name: str, customer_name: str) -> str:
    """Stage a proposed booking in the session buffer. Does NOT write to the database yet.
    
    Args:
        date: The booking date in YYYY-MM-DD format.
        hall_name: The name of the hall to reserve.
        customer_name: The name of the customer booking the hall.
    """
    pass

def commit_booking() -> str:
    """Commit the previously staged booking in the session buffer to the database.
    This finalizes the booking.
    """
    pass


class AgentOrchestrator:
    """
    Core orchestrator that runs the LLM execution loop, manages bilingual routing,
    executes isolated function-calling tools, and returns sanitized text responses.
    Uses the modern Google Gen AI Python SDK.
    """
    
    def __init__(self):
        # Tools will be registered here (isolated function maps)
        self.tools_registry = {}
        
        # Initialize Gemini Client (Resolving key from settings)
        api_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY
        if api_key == "mock_llm_key" or not api_key:
            api_key = None
            
        self.client = genai.Client(api_key=api_key)
        logger.info("Google Gen AI Client (Gemini) initialized.")

    def register_tool(self, name: str, tool_func):
        self.tools_registry[name] = tool_func
        logger.info(f"Registered tool: {name}")

    async def process_user_message(self, session: CallSession, user_text: str) -> str:
        """
        Main interface to process incoming user transcripts.
        """
        # 1. Bilingual language detection/switch helper
        # Detect if input contains Tamil characters (Unicode block: \u0b80 to \u0bff)
        has_tamil = any('\u0b80' <= char <= '\u0bff' for char in user_text)
        if has_tamil:
            session.language = "ta"
            logger.info(f"Session {session.session_id} dynamically switched language to Tamil")
        else:
            # If the user speaks in English / Latin script, automatically switch to English
            session.language = "en"
            logger.info(f"Session {session.session_id} dynamically switched language to English")

        # 2. Add message to session history
        session.add_to_history("user", user_text)

        # 3. Apply input guardrails (Get System Prompt for current language)
        system_instruction = guardrail_layer.inject_guardrails([], session.language)[0]["content"]

        # 4. Map CallSession history to Gemini Content structures
        gemini_contents = []
        for msg in session.history:
            if msg["role"] == "user":
                gemini_contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
            elif msg["role"] == "assistant":
                gemini_contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

        logger.info(f"Invoking Gemini ({settings.LLM_MODEL}) with tools and temperature {settings.LLM_TEMPERATURE}")

        tools_list = [check_availability, get_pricing, stage_booking, commit_booking]
        response_text = ""

        try:
            # 5. Call Gemini API with Tool Declarations & Low Temp Config
            response = self.client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=gemini_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=settings.LLM_TEMPERATURE,
                    tools=tools_list,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )
            )

            # 6. Parse and route native function calls manually for tool isolation
            if response.function_calls:
                function_call = response.function_calls[0]
                tool_name = function_call.name
                tool_args = function_call.args or {}
                
                logger.info(f"Gemini requested tool call: {tool_name} with args {tool_args}")
                
                if tool_name in self.tools_registry:
                    # Execute bounded tool (Passes session to support Propose-and-Commit pattern)
                    tool_result = await self.tools_registry[tool_name](session, **tool_args)
                    
                    # Append tool result to history
                    session.add_to_history("system", f"Tool {tool_name} returned: {tool_result}")
                    
                    # Follow-up invocation to explain tool results naturally to the user
                    followup_contents = list(gemini_contents)
                    followup_contents.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=f"System Notification: Tool '{tool_name}' executed. Result: {tool_result}. Formulate a 1-2 sentence response to the user.")]
                        )
                    )
                    
                    followup_response = self.client.models.generate_content(
                        model=settings.LLM_MODEL,
                        contents=followup_contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=settings.LLM_TEMPERATURE
                        )
                    )
                    response_text = followup_response.text or ""
                else:
                    response_text = f"Tool '{tool_name}' requested but not registered."
            else:
                response_text = response.text or ""

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
            if session.language == "ta":
                response_text = "மன்னிக்கவும், தகவல் பரிமாற்றத்தில் பிழை ஏற்பட்டுள்ளது."
            else:
                response_text = "I apologize, there was an issue processing your request."

        # 7. Apply output guardrails (Limit response length)
        sanitized_response = guardrail_layer.post_process_response(response_text)

        # 8. Save agent response to session history
        session.add_to_history("assistant", sanitized_response)

        return sanitized_response

# Global Singleton Agent Orchestrator
agent_orchestrator = AgentOrchestrator()

# Import tools package to execute registration decorators
import app.tools
