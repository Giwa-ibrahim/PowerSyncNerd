import logging, os
from langchain_ollama import OllamaLLM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger= logging.getLogger("ollama_api")

LLM_TEMPERATURE= float(os.getenv("TEMPERATURE"))
LLAMA_MODEL= os.getenv("LLAMA_MODEL")
LLAMA_API_URL= os.getenv("LLAMA_API_URL")

def ollama_client(model_name: str = LLAMA_MODEL) -> OllamaLLM:
    """
    Initializes and returns an Ollama LLM client.

    Args:
        model_name (str): The name of the Ollama model to use. Default is "llama2".

    Returns:
        OllamaLLM: An instance of the OllamaLLM client.
    """
    try:
        llm = OllamaLLM(
            model=model_name, 
            base_url=LLAMA_API_URL,
            temperature=LLM_TEMPERATURE,
            num_ctx=4096,
            num_predict=512)
        logger.info(f"Ollama LLM client initialized with model: {model_name}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Ollama LLM client: {e}")
        raise