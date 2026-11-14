
import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from core.project_builder import generate_project_files, create_project
from core.project_runner import ProjectRunner

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

st.set_page_config(
    page_title="NOVA",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 NOVA")
st.caption("Your Personal AI Assistant and Project Developer")

if not API_KEY:
    st.error("Gemini API key not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

SYSTEM_INSTRUCTION = """
You are NOVA, a helpful personal AI assistant.

Help with:
1. Software development
2. Python and SQL
3. Project planning
4. Research
5. Daily task management

Be friendly, practical and concise.
"""

# SESSION STATE

defaults = {
    "messages": [],
    "project_directory": None,
    "project_runner": None,
    "project_output": "",
    "project_status": "",
    "error_explanation": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# TABS

chat_tab, build_tab = st.tabs([
    "💬 Chat with NOVA",
    "🛠️ Build & Run a Project"
])


# CHAT SECTION

with chat_tab:

    st.subheader("Chat with NOVA")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask NOVA anything...")

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            try:

                history = st.session_state.messages[-10:]

                contents = [
                    {
                        "role": (
                            "user" if item["role"] == "user"
                            else "model"
                        ),
                        "parts": [{"text": item["content"]}]
                    }
                    for item in history
                ]

                response = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        max_output_tokens=1200
                    )
                )

                answer = response.text or "I couldn't generate a response."

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as exc:
                st.error(f"NOVA error: {exc}")


# PROJECT BUILDER

with build_tab:

    st.subheader("🛠️ NOVA Project Builder")

    description = st.text_area(
        "Describe the project you want NOVA to build",
        placeholder="Example: Create a Python calculator...",
        height=130
    )

    requested_name = st.text_input(
        "Project name (optional)"
    )

    if st.button("🚀 Generate Project", type="primary"):

        if not description.strip():

            st.warning("Please describe your project.")

        else:

            try:

                with st.spinner("NOVA is generating your project..."):

                    generated = generate_project_files(
                        client,
                        description,
                        requested_name.strip() or None,
                        MODEL
                    )

                saved = create_project(
                    generated["project_name"],
                    generated["files"]
                )

                old_runner = st.session_state.project_runner

                if old_runner:
                    old_runner.stop()

                st.session_state.project_directory = (
                    saved["project_directory"]
                )

                st.session_state.project_runner = None
                st.session_state.project_output = ""
                st.session_state.project_status = "Project files created."
                st.session_state.error_explanation = ""

                st.success("Project created successfully!")

                st.rerun()

            except Exception as exc:
                st.error(f"Project generation failed: {exc}")


    # GENERATED PROJECT DETAILS

    project_dir = st.session_state.project_directory

    if project_dir:

        st.divider()

        st.subheader("📁 Generated Project")

        st.code(str(project_dir))

        if os.path.isdir(project_dir):

            for name in sorted(os.listdir(project_dir)):
                st.write(f"📄 {name}")


        # PROJECT EXECUTION CONSOLE

        st.divider()

        st.subheader("▶️ Project Execution Console")

        st.caption(
            "Run your generated Python project inside Docker."
        )

        runner = st.session_state.project_runner

        if runner:

            pending = runner.get_output()

            if pending:
                st.session_state.project_output += pending

            status = runner.get_status()

        else:

            status = {
                "running": False,
                "exit_code": None,
                "error_detected": False,
                "error_details": ""
            }

        running = status["running"]

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "▶️ Start Project" if runner is None
                else "🔄 Restart Project",
                type="primary",
                disabled=running,
                use_container_width=True
            ):

                new_runner = ProjectRunner(project_dir)

                result = new_runner.start()

                if result["success"]:

                    st.session_state.project_runner = new_runner
                    st.session_state.project_output = ""
                    st.session_state.error_explanation = ""
                    st.session_state.project_status = result["message"]

                    st.rerun()

                else:
                    st.error(result["error"])

        with col2:

            if st.button(
                "🔄 Refresh Console",
                use_container_width=True
            ):

                if runner:

                    pending = runner.get_output()

                    if pending:
                        st.session_state.project_output += pending

                st.rerun()


        # STATUS AND OUTPUT

        runner = st.session_state.project_runner

        if runner:

            status = runner.get_status()
            running = status["running"]

            if running:

                st.success("Project is running.")

            elif status["exit_code"] is not None:

                if status["exit_code"] == 0:
                    st.info("Project finished successfully.")

                elif status["exit_code"] == 130:
                    st.info("Project was stopped.")

                else:
                    st.error(
                        f"Project exited with code {status['exit_code']}."
                    )


            # ERROR DETECTION

            if status["error_detected"]:

                st.error("⚠️ NOVA detected a possible project error.")

                details = status.get("error_details", "")

                if details:

                    with st.expander(
                        "Detected Error Details",
                        expanded=True
                    ):
                        st.code(details, language="text")


            # TERMINAL OUTPUT

            st.markdown("**Terminal Output**")

            if st.session_state.project_output:

                st.code(
                    st.session_state.project_output,
                    language="text"
                )

            else:

                st.info("No output captured yet. Click Refresh Console.")


            # INTERACTIVE INPUT

            if running:

                with st.form(
                    "project_input_form",
                    clear_on_submit=True
                ):

                    user_input = st.text_input(
                        "Send input to project",
                        placeholder="Type your input..."
                    )

                    send = st.form_submit_button("Send Input")

                    if send:

                        if not user_input:

                            st.warning("Please enter some input.")

                        else:

                            result = runner.send_input(user_input)

                            if result["success"]:
                                st.success("Input sent successfully.")

                            else:
                                st.error(result["error"])

                            st.rerun()


                # STOP PROJECT

                if st.button("⏹️ Stop Project"):

                    result = runner.stop()

                    st.session_state.project_status = result.get(
                        "message",
                        result.get("error", "")
                    )

                    st.rerun()


            # GEMINI ERROR EXPLANATION

            if status["error_detected"]:

                if st.button("✨ Ask NOVA to Explain the Error"):

                    try:

                        with st.spinner("NOVA is analyzing the error..."):

                            response = client.models.generate_content(
                                model=MODEL,
                                contents=(
                                    "Explain this programming error in "
                                    "simple language. Identify its likely "
                                    "cause and suggest a safe fix. "
                                    "Do not claim to edit files.\n\n"

                                    "Terminal output:\n"
                                    + st.session_state.project_output

                                    + "\nDetected error:\n"
                                    + status.get("error_details", "")
                                ),
                                config=types.GenerateContentConfig(
                                    max_output_tokens=1200
                                )
                            )

                        st.session_state.error_explanation = (
                            response.text or "No explanation returned."
                        )

                    except Exception as exc:

                        st.session_state.error_explanation = str(exc)


                if st.session_state.error_explanation:

                    st.markdown("**NOVA's Error Explanation**")

                    st.markdown(
                        st.session_state.error_explanation
                    )


        if st.session_state.project_status:
            st.caption(st.session_state.project_status)
