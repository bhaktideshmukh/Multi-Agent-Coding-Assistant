import streamlit as st
import os
import shutil
from dotenv import load_dotenv
from graph import app

# Load environment variables (.env file)
load_dotenv()

st.set_page_config(page_title="Multi-Agent Coder Buddy", page_icon="🤖")

st.title("🤖 Multi-Agent Coding Assistant")
st.markdown("Built with LangGraph & Llama-3.")

user_request = st.text_area("What would you like to build?", placeholder="e.g., Build a calculator web app with HTML, CSS, and JS")

if st.button("Build Project"):
    if not os.getenv("GROQ_API_KEY"):
        st.error("Please set your GROQ_API_KEY in the .env file.")
        st.stop()
        
    if not user_request:
        st.warning("Please enter a project description.")
        st.stop()
        
    # Clear previous workspace
    if os.path.exists("workspace"):
        shutil.rmtree("workspace")
    os.makedirs("workspace")
    
    initial_state = {"user_request": user_request}
    
    with st.status("Agents at work...", expanded=True) as status:
        # Stream the output from the graph
        for output in app.stream(initial_state):
            for key, value in output.items():
                if key == "planner":
                    st.write("✅ **Planner Agent:** Created project plan.")
                    with st.expander("View Plan"):
                        st.write(value["plan"])
                        
                elif key == "architect":
                    st.write("✅ **Architect Agent:** Defined file structure.")
                    with st.expander("View Architecture"):
                        st.json(value["architecture"])
                        
                elif key == "coder":
                    if "status" in value and value["status"] == "Coding Complete":
                        st.write("✅ **Coder Agent:** Finished writing all files.")
                    else:
                        current_index = value["current_file_index"] - 1
                        file_name = value["architecture"][current_index]["file_name"]
                        st.write(f"💻 **Coder Agent:** Wrote `{file_name}`.")
                        with st.expander(f"View Code: {file_name}"):
                            st.code(value["architecture"][current_index]["code"])
                            
        status.update(label="Project generation complete!", state="complete", expanded=False)
        
    st.success("Your project is ready in the `workspace` folder!")
    
    # Create a ZIP file for easy downloading
    shutil.make_archive("generated_project", "zip", "workspace")
    with open("generated_project.zip", "rb") as f:
        st.download_button("Download Project (ZIP)", data=f, file_name="generated_project.zip", mime="application/zip")
