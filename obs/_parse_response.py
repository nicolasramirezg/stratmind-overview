import json

def _parse_response(self, response, area_name: str) -> list[str]:
    """
    Parse the model's response and extract a list of valid subtasks for the given area.
    Falls back to simple line-based parsing if JSON is malformed.
    """
    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)

        if isinstance(data, dict) and "area" in data and "subtasks" in data:
            subtasks_raw = data["subtasks"]

            if isinstance(subtasks_raw, list):
                valid_subtasks = []
                for s in subtasks_raw:
                    if isinstance(s, str) and s.strip():
                        valid_subtasks.append(s.strip())
                return valid_subtasks

        # fallback: return whole content as single subtask if format is incorrect
        return [content.strip()]

    except json.JSONDecodeError:
        # fallback: extract lines as subtasks
        fallback_subtasks = []
        for line in content.splitlines():
            line = line.strip()
            if line:
                fallback_subtasks.append(line.lstrip("-• "))
        return fallback_subtasks
