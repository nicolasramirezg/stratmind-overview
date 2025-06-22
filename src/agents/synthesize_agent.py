import os
from openai import OpenAI

class SynthesizeAgent:
    def __init__(self, model="gpt-4o", temperature=0.7):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def synthesize(self, history):
        prompt = (
            "Analyze the following conversation and extract the final, clarified task specification "
            "and the expected output. Return your answer in exactly this format:\n\n"
            "Task: <the detailed task>\n"
            "Expected Output: <the expected output description. Do not leave this blank. If the user was vague, infer a reasonable output.>\n"
            "Conversation:\n"
        )
        conversation = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in history]
        )
        full_prompt = prompt + conversation

        messages = [
            {"role": "system", "content": (
                "You are an expert agent that reads conversations and extracts the clarified task and expected output."
            )},
            {"role": "user", "content": full_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        output_text = response.choices[0].message.content.strip()
        # Parse result
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