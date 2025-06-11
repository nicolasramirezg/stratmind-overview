from string import Template
import os

def load_prompt(rel_path: str, variables: dict) -> str:
    """
    Carga un archivo de prompt con placeholders y realiza la sustitución usando
    Template.substitute().

    Args:
        rel_path (str): Ruta relativa desde el directorio raíz del proyecto.
        variables (dict): Diccionario con las claves a sustituir en el texto.

    Returns:
        str: Prompt con las variables interpoladas.
    """
    # Obtiene ruta absoluta desde donde se ejecuta el script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Sube un nivel para salir de /utils y llegar a /src
    project_root = os.path.abspath(os.path.join(base_dir, ".."))

    # Construye ruta absoluta al archivo de texto
    full_path = os.path.join(project_root, rel_path)

    with open(full_path, encoding="utf-8") as f:
        template = Template(f.read())
        return template.substitute(variables)
