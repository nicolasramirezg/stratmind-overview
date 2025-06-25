import os
import json
from datetime import datetime
from .task_to_dict import task_to_dict

def export_task_tree(root_task, manager, out_name="task_tree", output_dir="output"):
    """
    Exports the task tree to a JSON file with a custom name and timestamp.

    Args:
        root_task: The root task of the tree.
        manager: The TaskManager instance with all tasks.
        out_name: Prefix for the output file name.
        output_dir: Directory where the JSON will be saved.
    """
    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{out_name}.json"

    # Ensure the output directory exists
    full_dir = os.path.join(os.getcwd(), output_dir)
    os.makedirs(full_dir, exist_ok=True)
    output_path = os.path.join(full_dir, filename)

    # Convert the task tree to a serializable dict
    tree_json = task_to_dict(root_task)

    # Write the JSON to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Task tree exported to: {output_path}")


