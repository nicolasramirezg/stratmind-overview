import streamlit as st
import os
import json

def render_task(task, parent_results=None, level=0):
    title = task.get('title', '[No title]')
    indent = " " * level  # U+2003 for soft indent

    # Mostrar el expander para esta tarea
    with st.expander(f"{indent}📁 {title}", expanded=(level <= 1)):
        st.markdown(f"**📝 Description:**\n{task.get('description', '-')}")
        st.markdown(f"**🎯 Expected Output:**\n{task.get('expected_output', '-')}")

        # Mostrar prompt si existe
        prompt = task.get("prompt", {})
        if "user" in prompt:
            st.markdown("**📤 Prompt:**")
            st.code(prompt["user"], language="text")

        # Mostrar result (directo o heredado)
        result = task.get("result")
        if not result and parent_results:
            result = parent_results.get(title)

        st.markdown("**✅ Result:**")
        if result:
            if isinstance(result, dict):
                for k, v in result.items():
                    st.markdown(f"**{k}**")
                    st.code(v, language="text")
            else:
                st.code(result, language="text")
        else:
            st.info("⏳ No result available yet.")

    # Subtareas (fuera del expander del padre)
    subtasks = task.get("subtasks", [])
    child_results = task.get("result") if isinstance(task.get("result"), dict) else None
    for sub in subtasks:
        render_task(sub, parent_results=child_results, level=level + 1)

# === MAIN ===
st.set_page_config(page_title="🌐 Árbol de tareas multiagente", layout="wide")
st.title("🧠 Visualizador jerárquico de tareas multiagente")

# Ruta relativa al archivo JSON
json_path = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "output", "task_treebogota4.json"
))

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            task_data = json.load(f)
            render_task(task_data)
        except Exception as e:
            st.error(f"❌ Error al cargar el JSON: {e}")
else:
    st.warning(f"⚠️ No se encontró el archivo en: `{json_path}`")
