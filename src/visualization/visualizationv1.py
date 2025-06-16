import streamlit as st
import json
from pyvis.network import Network

st.set_page_config(page_title="Árbol de Agentes - Grafo Interactivo", layout="wide")
st.title("🌳 Visualización Impactante del Árbol de Agentes (Grafo Interactivo)")

json_path = "output/20250616_235044_task_tree_bogota.json"

@st.cache_data
def load_tree(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

data = load_tree(json_path)

def add_nodes_edges(net, task, parent_id=None):
    label = task.get("title", "Sin título")
    tooltip = f"<b>{label}</b><br>"
    tooltip += f"<b>Descripción:</b> {task.get('description', '')}<br>"
    tooltip += f"<b>Expected Output:</b> {task.get('expected_output', '')}<br>"
    tooltip += f"<b>Execution Type:</b> {task.get('execution_type', '')}<br>"
    if task.get("dependencies"):
        tooltip += f"<b>Dependencias:</b> {', '.join(task['dependencies'])}<br>"
    if "result" in task and task["result"]:
        result_str = str(task["result"])
        tooltip += f"<b>Resultado:</b> {result_str[:300]}{'...' if len(result_str)>300 else ''}<br>"
    color = "#6fa8dc" if parent_id is None else "#b6d7a8"
    net.add_node(task["task_id"], label=label, title=tooltip, color=color, shape="dot", size=25)
    if parent_id:
        net.add_edge(parent_id, task["task_id"], color="#999999")
    for sub in task.get("subtasks", []):
        add_nodes_edges(net, sub, task["task_id"])

# Crear el grafo
net = Network(height="700px", width="100%", bgcolor="#222222", font_color="white", directed=True)
add_nodes_edges(net, data)

# Opciones visuales avanzadas
net.set_options("""
var options = {
  "nodes": {
    "borderWidth": 2,
    "shadow": true
  },
  "edges": {
    "color": {
      "inherit": true
    },
    "smooth": false
  },
  "interaction": {
    "hover": true,
    "navigationButtons": true,
    "multiselect": true,
    "tooltipDelay": 100
  },
  "physics": {
    "enabled": true,
    "barnesHut": {
      "gravitationalConstant": -8000,
      "centralGravity": 0.3,
      "springLength": 120,
      "springConstant": 0.04,
      "damping": 0.09,
      "avoidOverlap": 1
    }
  }
}
""")

# Renderiza el grafo en Streamlit
net.save_graph("graph.html")
with open("graph.html", "r", encoding="utf-8") as f:
    html = f.read()
st.components.v1.html(html, height=750, scrolling=True)