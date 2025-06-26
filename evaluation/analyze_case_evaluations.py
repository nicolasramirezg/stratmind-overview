import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
from datetime import datetime

def load_task_tree(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_tree(tree):
    def walk(node, depth=0):
        stats["total_nodes"] += 1
        stats["max_depth"] = max(stats["max_depth"], depth)
        if node.get("execution_type", "llm") == "llm":
            stats["llm_tasks"] += 1
        if not node.get("subtasks"):
            stats["leaf_count"] += 1
        else:
            child_counts.append(len(node["subtasks"]))
            for child in node["subtasks"]:
                walk(child, depth + 1)

    stats = {
        "total_nodes": 0,
        "max_depth": 0,
        "llm_tasks": 0,
        "leaf_count": 0,
        "area_count": 0
    }
    child_counts = []

    stats["area_count"] = len(tree.get("subtasks", []))
    walk(tree)

    stats["avg_children_per_node"] = np.mean(child_counts) if child_counts else 0
    stats["llm_task_ratio"] = stats["llm_tasks"] / stats["total_nodes"] if stats["total_nodes"] else 0
    stats["result_coverage"] = compute_result_coverage(tree)
    return stats

def compute_result_coverage(tree):
    results = []

    def collect(node):
        if "result" in node:
            results.append(node["result"] is not None and node["result"] != "")
        for child in node.get("subtasks", []):
            collect(child)

    collect(tree)
    return sum(results) / len(results) if results else 0

def main():
    output_dir = "output"
    results = []

    for filename in os.listdir(output_dir):
        if filename.endswith(".json") and "CASE" in filename:
            file_path = os.path.join(output_dir, filename)
            tree = load_task_tree(file_path)
            stats = analyze_tree(tree)

            # Extraer el case_id correctamente del nombre
            case_id_match = re.search(r"(CASE\d+)", filename)
            case_id = case_id_match.group(1) if case_id_match else "unknown"

            stats["case_id"] = case_id
            stats["file"] = filename
            results.append(stats)

    df = pd.DataFrame(results)
    df = df.sort_values("case_id").reset_index(drop=True)

    print("\n=== Resultados comparativos ===")
    print(df[["case_id", "total_nodes", "max_depth", "area_count", "avg_children_per_node",
              "leaf_count", "llm_task_ratio", "result_coverage"]])

    df.to_csv("evaluation/evaluation_summary_cases.csv", index=False)

    plot_radar(df)

def plot_radar(df):
    metrics = ["total_nodes", "max_depth", "area_count", "avg_children_per_node",
               "leaf_count", "llm_task_ratio", "result_coverage"]

    df_norm = df.copy()
    df_norm[metrics] = (df[metrics] - df[metrics].min()) / (df[metrics].max() - df[metrics].min())

    labels = metrics
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for i, row in df_norm.iterrows():
        values = row[labels].tolist()
        values += values[:1]
        ax.plot(angles, values, label=row["case_id"])
        ax.fill(angles, values, alpha=0.1)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title("Comparativa de árboles por caso")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=3)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
