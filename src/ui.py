import streamlit as st
import json
from streamlit_tree_select import tree_select

st.set_page_config(page_title="Task Tree", layout="wide")
st.title("Task Tree (Interactive)")

json_path = "c:/Users/nicol/Documents/MEBDS/TFM/git/agentLLM/output/task_treecrossfit2.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def build_tree(task):
    node = {
        "label": task["title"],
        "value": task["task_id"],
        "children": [build_tree(sub) for sub in task.get("subtasks", [])]
    }
    return node

tree_data = [build_tree(data)]

selected = tree_select(
    tree_data,
    key="tree"
)

def find_task(task, task_id):
    if task["task_id"] == task_id:
        return task
    for sub in task.get("subtasks", []):
        found = find_task(sub, task_id)
        if found:
            return found
    return None

def show_result(result, level=0):
    indent = "&nbsp;" * 4 * level
    if isinstance(result, dict):
        if not result:
            st.markdown(f"{indent}_No result available for this area._")
        else:
            for k, v in result.items():
                st.markdown(f"{indent}- **{k}:**")
                show_result(v, level + 1)
    elif isinstance(result, list):
        for item in result:
            show_result(item, level + 1)
    elif result is not None:
        st.markdown(f"{indent}{result}")
    else:
        st.markdown(f"{indent}_No result available for this task._")

if selected and "value" in selected:
    selected_task = find_task(data, selected["value"])
    if selected_task:
        st.subheader(selected_task["title"])
        st.markdown(f"**Description:** {selected_task.get('description', '')}")
        st.markdown(f"**Expected Output:** {selected_task.get('expected_output', '')}")
        # Mostrar resultado si existe, o resultados de subtareas si no hay resultado propio
        if 'result' in selected_task and selected_task['result'] is not None:
            st.markdown("**Result:**")
            show_result(selected_task['result'])
        elif 'subtasks' in selected_task and selected_task['subtasks']:
            st.markdown("**Aggregated Results from Subtasks:**")
            for sub in selected_task['subtasks']:
                st.markdown(f"- **{sub['title']}**")
                if 'result' in sub and sub['result'] is not None:
                    show_result(sub['result'], 1)
                else:
                    st.markdown("&nbsp;" * 4 + "_No result available for this subtask._")
        else:
            st.markdown("_No result available for this task._")
        if 'execution_type' in selected_task:
            st.markdown(f"**Execution Type:** {selected_task['execution_type']}")
        if 'responsibilities' in selected_task and selected_task['responsibilities']:
            st.markdown(f"**Responsibilities:** {', '.join(selected_task['responsibilities'])}")
        if 'dependencies' in selected_task and selected_task['dependencies']:
            st.markdown(f"**Dependencies:** {', '.join(selected_task['dependencies'])}")