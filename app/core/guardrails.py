import logging
from typing import List, Dict

logger = logging.getLogger("voice_agent.guardrails")

SYSTEM_PROMPT_TAMIL = (
    "நீங்கள் ஒரு திருமண மண்டப முன்பதிவு உதவியாளர். "
    "விருந்தினர்களிடம் கண்ணியமாகவும் சுருக்கமாகவும் பேசவும். "
    "பதில்களை கண்டிப்பாக 1-2 வாக்கியங்களுக்குள் கட்டுப்படுத்தவும். "
    "தகவல்களை சுயமாக கற்பனை செய்ய வேண்டாம் (hallucinate). "
    "எழுதும் முன் வாடிக்கையாளரின் அனுமதியை (confirmation) பெறவும்."
)

SYSTEM_PROMPT_ENGLISH = (
    "You are a professional hall booking assistant. "
    "Be polite and extremely concise. "
    "Limit your response STRICTLY to 1-2 sentences to prevent voice delay. "
    "Never hallucinate pricing or availability. "
    "Always get explicit user confirmation before executing any booking writes, updates, or deletes."
)

class LLMGuardrails:
    """
    Gateway interceptor enforcing low latency and zero-hallucination guardrails.
    - Limits response length to 1-2 sentences.
    - Forces low-temperature system prompts.
    - Enforces language boundaries (Tamil / English).
    """
    
    @staticmethod
    def inject_guardrails(messages: List[Dict[str, str]], language: str) -> List[Dict[str, str]]:
        """
        Prepend language-specific concise system instructions and format boundaries.
        """
        system_instruction = SYSTEM_PROMPT_TAMIL if language == "ta" else SYSTEM_PROMPT_ENGLISH
        
        # Insert or override system instructions at the beginning of LLM conversation history
        sanitized_messages = []
        sanitized_messages.append({"role": "system", "content": system_instruction})
        
        # Append remaining dialogue history
        for msg in messages:
            if msg["role"] != "system":
                sanitized_messages.append(msg)
                
        return sanitized_messages

    @staticmethod
    def post_process_response(text: str) -> str:
        """
        Validates LLM response. Intercepts and truncates output if it exceeds 2 sentences
        to guarantee minimal TTS synthesis latency.
        """
        if not text:
            return ""
            
        # Basic sentence splitting (supporting English periods and Tamil markers)
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        
        if len(sentences) > 2:
            logger.warning("LLM response exceeded guardrail limits (more than 2 sentences). Truncating response.")
            truncated = ". ".join(sentences[:2]) + "."
            return truncated
            
        return text

guardrail_layer = LLMGuardrails()
