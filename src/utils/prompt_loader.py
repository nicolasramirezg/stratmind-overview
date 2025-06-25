from string import Template
import os

def load_prompt(rel_path: str, variables: dict) -> str:
    """
    Loads a prompt file with placeholders and performs variable substitution using Template.substitute().

    Args:
        rel_path (str): Relative path from the project root directory to the prompt file.
        variables (dict): Dictionary with keys to substitute in the prompt text.

    Returns:
        str: The prompt with variables interpolated.
    """
    # Get the absolute path of the current file (this script)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up one level to reach /src from /src/utils
    project_root = os.path.abspath(os.path.join(base_dir, ".."))

    # Build the absolute path to the prompt text file
    full_path = os.path.join(project_root, rel_path)

    # Read the prompt file and substitute variables
    with open(full_path, encoding="utf-8") as f:
        template = Template(f.read())
        return template.substitute(variables)
