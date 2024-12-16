import streamlit as st
from stream_tts_volce import render_volce_tts_ui
from stream_tts_edge import render_edge_tts_ui

# Define a function to display the main page with buttons for switching UIs
def main():
    st.sidebar.title("AI工具盒")
    
    # Create buttons or use selectbox for navigation
    ui_selection = st.sidebar.radio("TTS工具:", ("火山语音合成", "微软语音合成"))

    # Render the selected UI based on the button pressed
    if ui_selection == "火山语音合成":
        render_volce_tts_ui()
    elif ui_selection == "微软语音合成":
        render_edge_tts_ui()

# Call the main function
if __name__ == "__main__":
    main()

