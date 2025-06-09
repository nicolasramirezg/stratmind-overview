import os
import json
from datetime import datetime

def save_run(task_description: str, decomposition: dict, log_dir: str = "log"):
    # Asegurar que la carpeta existe
    os.makedirs(log_dir, exist_ok=True)

    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{timestamp}.json"
    path = os.path.join(log_dir, filename)

    # Preparar el contenido a guardar
    session = {
        "task": task_description,
        "decomposition": decomposition
    }

    # Guardar en JSON
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)

    print(f"Session saved to: {path}")


