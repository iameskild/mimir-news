import os
from typing import Any, Dict
import requests
from enum import Enum
from abc import ABC
from pathlib import Path

import openai
from pydantic import BaseModel
from elevenlabs import ElevenLabs
from prompt_poet import Prompt

from .models import ResearchDetails


class LLM(Enum):
    PERPLEXITY = "perplexity"
    OPENAI = "openai"


# Drew - male voice, good for news
VOICE_ID = "29vD33N1CtxCmqQRPOHJ"


### Base Agent ###


class Agent(ABC):
    """
    An agent is a class that can call an LLM.
    """

    def __init__(self, name: str, prompt_template: str, llm: LLM = LLM.OPENAI):
        self.name = name
        self.prompt_template = self._load_prompt_template(prompt_template)
        self.llm = llm

    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load the prompt template from the prompts directory.
        """
        prompts_dir = Path(__file__).parent / "prompts"
        template_path = prompts_dir / f"{template_name}.yaml"
        return template_path

    def _create_prompt(self, input: BaseModel) -> Prompt:
        """
        Create a Prompt object with the template and input data.
        """
        template_data = {**input.model_dump()}
        return Prompt(template_path=self.prompt_template, template_data=template_data)

    def call_llm(
        self,
        input: BaseModel,
        format_output: bool = True,
        **kwargs,
    ) -> Dict[str, Any] | BaseModel | str:
        """
        Call the LLM with the input.
        """
        prompt = self._create_prompt(input)

        if self.llm == LLM.PERPLEXITY:
            output = call_perplexity_api(prompt.messages, **kwargs)
        elif self.llm == LLM.OPENAI:
            output = call_openai_api(prompt.messages, **kwargs)
        else:
            raise ValueError(f"LLM {self.llm} not supported")

        if format_output:
            return self.format_output(output)
        else:
            return output

    def format_output(self, output: str) -> BaseModel:
        """
        Format the output.
        """
        pass


### Researcher Agent ###


class Researcher(Agent):
    def __init__(self, llm: LLM = LLM.PERPLEXITY):
        super().__init__(
            name="Researcher",
            prompt_template="researcher",
            llm=llm,
        )

    def format_output(self, output: str) -> ResearchDetails:
        """
        Format the output.
        """
        if self.llm == LLM.PERPLEXITY:
            citations = output["citations"]
            content = output["choices"][0]["message"]["content"].split("</think>")[-1]
            return ResearchDetails(research=content, citations=citations)
        else:
            raise ValueError(f"LLM {self.llm} not supported")


### News Writer Agent ###


class NewsWriter(Agent):
    def __init__(self, llm: LLM = LLM.OPENAI):
        super().__init__(
            name="NewsWriter",
            prompt_template="news_writer",
            llm=llm,
        )

    def format_output(self, output: str) -> str:
        """
        Format the output.
        """
        return output


### AI Models ###


def call_perplexity_api(
    messages: list, model: str = "sonar-reasoning-pro"
) -> Dict[str, Any]:
    """
    Call the perplexity API.
    """
    url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise Exception("PERPLEXITY_API_KEY is not set")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "messages": messages,
        "model": model,
        "frequency_penalty": 1,
        "max_tokens": None,
        "presence_penalty": 0,  # incompatible with `frequency_penalty`
        "response_format": None,
        "return_images": False,
        "return_related_questions": False,
        "search_domain_filter": None,
        "search_recency_filter": None,
        "stream": False,
        "temperature": 0.2,
        "top_p": 0.5,  # use either top_k or top_p, not both
        "top_k": None,  # use either top_k or top_p, not both
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(
                f"An error occurred while calling the perplexity API: {response.json()}"
            )
        return response.json()
    except Exception as e:
        raise Exception(f"An error occurred while calling the perplexity API: {e}")


def call_openai_api(messages: list, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Call the openai API.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise Exception("OPENAI_API_KEY is not set")
    client = openai.OpenAI(api_key=openai.api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


def call_eleven_labs_api(
    text: str, voice_id: str = VOICE_ID, save_path: str = None
) -> bytes:
    """
    Call the eleven labs API.
    """
    api_key = os.getenv("ELEVEN_LABS_API_KEY")
    if not api_key:
        raise Exception("ELEVEN_LABS_API_KEY is not set")
    client = ElevenLabs(api_key=api_key)
    response = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
    )
    # Convert generator to bytes
    audio_data = b"".join(response)

    if save_path:
        with open(save_path, "wb") as f:
            f.write(audio_data)
    return audio_data
