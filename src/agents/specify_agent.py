import os
from openai import OpenAI
from src.utils.prompt_loader import load_prompt


class SpecifyAgent:
    """
    Agent specialized in clarifying and specifying user tasks through interactive dialogue.
    Loads system prompts from external .txt files for flexibility.
    """

    def __init__(self, model="gpt-4o", temperature=0.7):
        """
        Initialize the SpecifyAgent with a given OpenAI model and temperature.

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

    @staticmethod
    def system_prompt():
        """
        Loads the system prompt from an external .txt file.

        Returns:
            str: The system prompt string.
        """
        return load_prompt("prompts/specify_agent/system.txt", {})

    @classmethod
    def initial_history(cls, user_input=None):
        """
        Builds the initial conversation history for the agent.

        Args:
            user_input (str, optional): The user's initial task description.

        Returns:
            list: List of message dicts for the conversation.
        """
        history = [{"role": "system", "content": cls.system_prompt()}]
        if user_input:
            history.append({"role": "user", "content": user_input})
        return history

    def get_response(self, history):
        """
        Gets a response from the LLM given the conversation history.

        Args:
            history (list): The conversation history as a list of message dicts.

        Returns:
            str: The LLM's response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=history,
            temperature=self.temperature
        )
        return response.choices[0].message.content.strip()

    def interactive_specification(self):
        """
        Runs an interactive loop to clarify and specify the user's task.
        The loop continues until the agent determines the task is fully specified
        or the user types 'finish'.

        Returns:
            list: The final conversation history.
        """
        history = self.initial_history()
        initial_task = input("Enter the initial task: ").strip()
        history.append({"role": "user", "content": initial_task})

        while True:
            agent_response = self.get_response(history)
            print("\nAgent:", agent_response)
            history.append({"role": "assistant", "content": agent_response})

            if "fully specified" in agent_response.lower():
                break

            user_input = input("User (type your answer or 'finish' to end): ").strip()
            if user_input.lower() == "finish":
                history.append({"role": "user", "content": user_input})
                break
            history.append({"role": "user", "content": user_input})

        return history