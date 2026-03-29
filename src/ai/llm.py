import logging, os
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("llm_api")

try:
    LLM_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
except (ValueError, TypeError):
    LLM_TEMPERATURE = 0.2

def get_llm_client(model_name: str = "llama-3.3-70b-versatile"):
    """
    Initializes and returns a Groq LLM client (Llama3) with a fallback to Google Gemini.
    """
    try:
        # Primary Model: Groq LLaMA 3
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            primary_llm = ChatGroq(
                temperature=LLM_TEMPERATURE,
                model_name=model_name,
                api_key=groq_api_key
            )
        else:
            primary_llm = None
            logger.warning("GROQ_API_KEY not found. Attempting to use fallback directly.")

        # Fallback Model: Google Gemini
        google_api_key = os.getenv("GEMINI_API_KEY")
        if google_api_key:
            fallback_llm = ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                temperature=LLM_TEMPERATURE,
                google_api_key=google_api_key
            )
        else:
            fallback_llm = None
            logger.warning("GEMINI_API_KEY not found.")

        # Compose routing
        if primary_llm and fallback_llm:
            llm_with_fallback = primary_llm.with_fallbacks([fallback_llm])
            logger.info("Groq LLM initialized with Gemini Fallback.")
            return llm_with_fallback
        elif primary_llm:
            logger.info("Groq LLM initialized safely (No Google Fallback available).")
            return primary_llm
        elif fallback_llm:
            logger.info("Gemini LLM initialized strictly (No Groq available).")
            return fallback_llm
        else:
            raise ValueError("No API Keys provided. Ensure GROQ_API_KEY or GEMINI_API_KEY is defined in .env")

    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        raise