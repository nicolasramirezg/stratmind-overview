import os
import json
from datetime import datetime
from .task_to_dict import task_to_dict  # si lo separas, si no, elimina esta línea
# from src.utils.task_exporter_txt import export_task_tree_txt

def export_task_tree(root_task, manager, out_name="task_tree", output_dir="output"):
    """
    Exporta el árbol de tareas a un archivo JSON con nombre personalizado + timestamp.

    Args:
        root_task: tarea raíz del árbol.
        manager: instancia de TaskManager con todas las tareas.
        out_name: prefijo del nombre del archivo.
        output_dir: carpeta donde se guarda el JSON.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{out_name}.json"

    full_dir = os.path.join(os.getcwd(), output_dir)
    os.makedirs(full_dir, exist_ok=True)
    output_path = os.path.join(full_dir, filename)

    tree_json = task_to_dict(root_task, manager)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Árbol de tareas exportado a: {output_path}")


