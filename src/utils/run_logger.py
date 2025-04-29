import json
import os
from datetime import datetime


def save_run(log_data: dict, output_dir: str = "logs"):
    """
    Guarda los resultados de una ejecución en un archivo JSON con timestamp.

    Args:
        log_data: Diccionario con los datos a guardar.
        output_dir: Carpeta donde guardar el archivo.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/run_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"\n Resultados guardados en: {filename}")
