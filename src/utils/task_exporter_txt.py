import os
from datetime import datetime

def export_task_tree_txt(root_task, manager, timestamp, output_dir="output"):
    """
    Exporta el árbol completo de tareas a un archivo .txt estructurado con jerarquía e incluye responsabilidades.

    Args:
        root_task: tarea raíz del árbol.
        manager: instancia de TaskManager con todas las tareas.
        output_dir: carpeta donde se guarda el archivo (por defecto 'output/').
        timestamp
    """

    filename = f"task_tree_{timestamp}.txt"

    full_dir = os.path.join(os.getcwd(), output_dir)
    os.makedirs(full_dir, exist_ok=True)
    output_path = os.path.join(full_dir, filename)

    def write_task(task, file, level=0):
        indent = "  " * level
        if level > 0:
            file.write(f"{indent}- {task.title}\n")
        else:
            # Título e introducción de la tarea raíz
            file.write(f"TAREA PRINCIPAL: {task.title}\n")
            if getattr(task, "intro", None):
                file.write(f"Descripción: {task.intro}\n")
            file.write("\n")

        # Añadir responsabilidades si existen
        if getattr(task, "responsibilities", []):
            for r in task.responsibilities:
                file.write(f"{indent}  · {r}\n")

        # Recorremos subtareas recursivamente
        children = [t for t in manager.tasks.values() if t.parent == task]
        for child in children:
            if child.area and level == 0:
                file.write(f"{indent}- Área: {child.area}\n")
                write_task(child, file, level + 1)
            else:
                write_task(child, file, level + 1)

    with open(output_path, "w", encoding="utf-8") as f:
        write_task(root_task, f)

    print(f"\n📄 Árbol de tareas exportado como texto a: {output_path}")
