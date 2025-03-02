import os
from typing import Any, Dict
from elevenlabs import ElevenLabs
import requests
from enum import Enum
from abc import ABC

from pydantic import BaseModel
import openai

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

    def __init__(self, name: str, role: str, base_prompt: str, llm: LLM = LLM.PERPLEXITY):
        self.name = name
        self.role = role
        self.base_prompt = base_prompt
        self.llm = llm
        self.question = None

    def _load_prompt(self, input: str | BaseModel) -> str:
        """
        Load the prompt with the input.
        """
        return self.base_prompt.format(input=input)

    def call_llm(
        self,
        input: BaseModel,
        format_output: bool = True,
        **kwargs,
    ) -> Dict[str, Any] | BaseModel:
        """
        Call the LLM with the input.
        """
        prompt = self._load_prompt(input)
        if self.llm == LLM.PERPLEXITY:
            output = call_perplexity_api(self.role, prompt, **kwargs)
        elif self.llm == LLM.OPENAI:
            output = call_openai_api(self.role, prompt, **kwargs)
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


research_role = """
You're a seasoned prediction markets researcher with a knack for uncovering the latest developments and trends in high-volume markets. 
Known for your ability to find the most relevant information and present it in a clear and concise manner, 
you excel at identifying key insights that can inform trading strategies and market predictions.
"""

research_prompt = """
Conduct thorough research on a particular prediction market question.
The question is:

```
{input.question}
```

And description is:

```
{input.description}
```
"""


class Researcher(Agent):
    def __init__(self):
        super().__init__(
            name="Researcher",
            role=research_role,
            base_prompt=research_prompt,
        )

    def format_output(self, output: str) -> ResearchDetails:
        """
        Format the output.
        """
        if self.llm == LLM.PERPLEXITY:
            citations = output["citations"]
            content = output['choices'][0]['message']['content'].split('</think>')[-1]
            return ResearchDetails(research=content, citations=citations)
        else:
            raise ValueError(f"LLM {self.llm} not supported")


news_writer_role = """
You're a seasoned news copywriter with a knack for writing news copy that are both informative and engaging.
The news copy will be used by the news anchor to read the news on the radio.
"""

news_writer_prompt = """
You are provided with the following research.
Write a news copy about the following prediction market question:

```
{input.research}
```

Please limit the news copy to 150 words.
"""

class NewsWriter(Agent):
    def __init__(self, llm: LLM = LLM.OPENAI):
        super().__init__(
            name="NewsWriter",
            role=news_writer_role,
            base_prompt=news_writer_prompt,
            llm=llm,
        )
    
    def format_output(self, output: str) -> str:
        """
        Format the output.
        """
        return output


### News Anchor ###




### AI Models ###


def call_perplexity_api(
    role: str, prompt: str, 
    model: str = "sonar-reasoning-pro"
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
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": prompt},
        ],
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


def call_openai_api(role: str, prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Call the openai API.
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise Exception("OPENAI_API_KEY is not set")
    client = openai.OpenAI(api_key=openai.api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": role}, {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_eleven_labs_api(text: str, voice_id: str = VOICE_ID, save_path: str = None) -> Dict[str, Any]:
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

