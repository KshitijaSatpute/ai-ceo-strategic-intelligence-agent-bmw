import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


class OllamaClient:
    def __init__(self, model_name=OLLAMA_MODEL):
        self.model_name = model_name

    def generate(self, prompt, temperature=0.0):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        try:
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=120
            )

            response.raise_for_status()
            data = response.json()

            return data.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            return (
                "Ollama is not running. Please start Ollama and run: "
                "ollama run qwen2.5:3b"
            )

        except Exception as error:
            return f"Ollama generation failed: {error}"


if __name__ == "__main__":
    client = OllamaClient()

    test_prompt = """
    You are a CEO strategy assistant.
    Write a short evidence-based CEO briefing for BMW EV strategy.
    """

    answer = client.generate(test_prompt)
    print(answer)