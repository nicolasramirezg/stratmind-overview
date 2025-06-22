import os
from openai import OpenAI

class SpecifyAgent:
    def __init__(self, model="gpt-4o", temperature=0.7):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def get_response(self, history):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=history,
            temperature=self.temperature
        )
        return response.choices[0].message.content.strip()

    def interactive_specification(self):
        history = [
            {"role": "system", "content": (
                "You are an expert agent specialized in clarifying and specifying user tasks. "
                "Your job is to ask concise, relevant questions to clarify the user's request. "
                "Ask only one question at a time. "
                "Do not execute or solve the task, only clarify. "
                "Do not provide options, suggestions, or examples unless the user asks. "
                "Do not insist if the user does not specify. "
                "Do not empathize or extend the conversation unnecessarily. "
                "When you have gathered all the necessary information and the task is fully specified, "
                "respond with: 'Thank you. The task is now fully specified.' and do not ask further questions. "
                "If the user types 'finish', you must also stop asking questions."
            )}
        ]
        initial_task = input("Enter the initial task: ").strip()
        history.append({"role": "user", "content": initial_task})

        while True:
            agent_response = self.get_response(history)
            print("\nAgent:", agent_response)
            history.append({"role": "assistant", "content": agent_response})

            # Si el agente indica que terminó, sal del bucle
            if "fully specified" in agent_response.lower():
                break

            user_input = input("User (type your answer or 'finish' to end): ").strip()
            if user_input.lower() == "finish":
                # Opcional: puedes agregar un mensaje final del usuario
                history.append({"role": "user", "content": user_input})
                break
            history.append({"role": "user", "content": user_input})

        return history