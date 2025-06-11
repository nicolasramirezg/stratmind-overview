import os
import json
from datetime import datetime
from .task_to_dict import task_to_dict  # si lo separas, si no, elimina esta línea
from src.utils.task_exporter_txt import export_task_tree_txt

def export_task_tree(root_task, manager, output_dir="output"):
    """
    Exporta el árbol de tareas a un archivo JSON en la carpeta especificada.

    Args:
        root_task: tarea raíz del árbol.
        manager: instancia de TaskManager con todas las tareas.
        output_dir: carpeta donde se guarda el JSON (por defecto 'output/').
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"task_tree_{timestamp}.json"

    full_dir = os.path.join(os.getcwd(), output_dir)
    os.makedirs(full_dir, exist_ok=True)
    output_path = os.path.join(full_dir, filename)

    tree_json = task_to_dict(root_task, manager)
    export_task_tree_txt(root_task, manager, timestamp)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Árbol de tareas exportado a: {output_path}")

