import logging
from datetime import datetime
from typing import List, Optional

from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter


def paginate_transcript(
    transcription_text, chunk_size=1000, chunk_overlap=0, logger=None
):
    """
    Generates a list of pages from the transcription text, suitable for inclusion within an LLM prompt.

    Args:
        transcription_text (str): The complete transcription text to be paginated.
        instructions (str): Instructions to be included at the beginning of each page.
        page_size (int, optional): The maximum number of lines per page. Defaults to 500.

    Returns:
        list: A list of page lists, where each page is a list of strings.
              Returns None if an error occurs.

    Raises:
        None

    Notes:
        This function is designed to generate chunks of the transcription text that can be
        passed to a large language model (LLM) for editing or summarization.
        It handles potential errors gracefully by logging the error and returning None.
    """
    try:
        logger.info(f"{datetime.now()}: Starting Pagination")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        texts = text_splitter.split_text(transcription_text)

        logger.info(f"{datetime.now()}: Pagination Completed Successfully")
        return texts

    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")
        return None  # Or raise the exception, depending on desired behavior


def send_transcript(
    transcript,
    instructions,
    model="llama3.1:8b",
    host="http://localhost:11434",
    num_ctx=4000,
    logger=None,
):
    """
    Edits the transcription text using an LLM.

    This function sends the transcription text to an LLM (e.g., Ollama) for editing.
    It supports specifying the LLM model and host URL.

    Args:
        transcript (str): The text of the transcription to edit.
        model (str, optional): The name of the LLM model to use. Defaults to "llama3.1:8b".
        host (str, optional): The URL of the host where the LLM is running. Defaults to "http://localhost:11434".
        num_ctx (int, optional): The number of tokens to use for the context window. Defaults to 4000.

    Returns:
        list: A list of strings, where each string is a line of the edited transcription text,
              or None if an error occurred.

    Raises:
        None
    """

    try:
        formatted_text = []

        logger.info(f"{datetime.now()}: Initializing Ollama")

        # Initialiaze Ollama
        llm = ChatOllama(model=model, temperature=0, base_url=host, num_ctx=num_ctx)

        logger.info(f"{datetime.now()}: Sending Transcript to Ollama for editing")
        for i in transcript:
            # Make the API call to Ollama
            messages = [
                ("system", instructions),
                ("human", i),
            ]
            ai_msg = llm.invoke(messages)

            formatted_text.append(ai_msg.content)

        logger.info(f"{datetime.now()}: Finished sending transcript to Ollama")

        return formatted_text

    except Exception as e:
        logger.error(f"{datetime.now()}: Error making API call: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
