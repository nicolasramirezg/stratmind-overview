import os
from openai import OpenAI
from src.utils.prompt_loader import load_prompt

class SynthesizeAgent:
    """
    Agent that synthesizes a clarified task and expected output from a conversation history.
    Loads prompts from external .txt files for flexibility.
    """

    def __init__(self, model="gpt-4o", temperature=0.7):
        """
        Initialize the SynthesizeAgent with a given OpenAI model and temperature.

        Args:
            model (str): The OpenAI model to use.
            temperature (float): The temperature for LLM responses.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def synthesize(self, history):
        """
        Synthesizes the clarified task and expected output from the conversation history.

        Args:
            history (list): The conversation history as a list of message dicts.

        Returns:
            dict: {
                "description": <clarified task>,
                "expected_output": <expected output>
            }
        """
        # Build the conversation string for the prompt
        conversation = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in history]
        )
        variables = {"conversation": conversation}

        # Load prompts from external .txt files
        system_prompt = load_prompt("prompts/synthesize_agent/system.txt", {})
        user_prompt = load_prompt("prompts/synthesize_agent/user.txt", variables)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Call the LLM to synthesize the task
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        output_text = response.choices[0].message.content.strip()

        # Parse the LLM output to extract the task and expected output
        lines = output_text.split("\n")
        task = ""
        expected_output = ""
        for line in lines:
            if line.lower().startswith("task:"):
                task = line.replace("Task:", "", 1).strip()
            elif line.lower().startswith("expected output:"):
                expected_output = line.replace("Expected Output:", "", 1).strip()
        if not expected_output:
            expected_output = "A detailed output describing the result of the clarified task."
        return {
            "description": task,
            "expected_output": expected_output
        }