import streamlit as st
import edge_tts
import asyncio
import os
import json
import volce_tts_stream

# 全局变量存储生成的音频文件列表
generated_files = []

def render_volce_tts_ui():
    # Ensure the generated_files list persists across reruns
    if "generated_files" not in st.session_state:
        st.session_state.generated_files = []
    # 删除生成的音频文件
    for file in st.session_state.generated_files:
        if os.path.exists(file):
            os.remove(file)
    st.session_state.generated_files.clear()
    # 加载语音数据
    with open("voice_volce.txt", "r", encoding="utf-8") as f:
        voice_data = json.load(f)

    # Create a dictionary of supported voices
    SUPPORTED_VOICES = {
        f"{voice['Gender']}-{voice['ShortName']}": voice['ShortName']
        for voice in voice_data
    }

    # Create a dictionary of supported voices
    VOICER_LIST = {
        f"{voice['Gender']}-{voice['ShortName']}": voice['Voicer']
        for voice in voice_data
    }

    SUPPORTED_EMOTIONS = {
        "happy": "happy - 开心",
        "sad": "sad - 悲伤",
        "angry": "angry - 生气",
        "scare": "scare - 害怕",
        "hate": "hate - 憎恨",
        "surprise": "surprise - 惊讶",
        "tear": "tear - 流泪",
        "novel_dialog": "novel_dialog - 小说对话",
        "narrator": "narrator - 叙述者",
        "narrator_immersive": "narrator_immersive - 沉浸式叙述者"
    }

    # 文本转语音
    async def VolceTextToSpeech(text, voices, emotion,speed, volume, pitch):
        output_file = "output.mp3"
        voices = VOICER_LIST[voices]
        audio_file_paths = await volce_tts_stream.volce_tts(text, voices, emotion, speed, volume, pitch, output_file)
        return audio_file_paths

    # 同步执行异步文本转语音函数
    def sync_VolceTextToSpeech(text, voices, voice_emotion,rate, volume, pitch):
        emotion="happy"
        for key, value in SUPPORTED_EMOTIONS.items():
            if value == voice_emotion:
                emotion = key
        return asyncio.run(VolceTextToSpeech(text, voices, emotion,rate, volume, pitch))


    # Streamlit App
    st.title("火山语音合成")

    # 输入文本
    text = st.text_area("输入文本(如果需要添加停顿 ，停顿位置加入<break time=\"500ms\"/> 500ms为时间，500毫秒>)", height=400)

    # 选择发音人
    voices = st.selectbox("选择发音人", list(SUPPORTED_VOICES.keys()), index=0)

    # 选择情感
    voice_emotion = st.selectbox("选择情感", list(SUPPORTED_EMOTIONS.values()), index=0)

    # 选择语速
    rate = st.slider("语速增减", 0.2, 3.0, 1.0, 0.1)

    # 选择音量
    volume = st.slider("音量增减", 0.1, 3.0, 1.0, 0.1)

    # 选择音调
    pitch = st.slider("音调增减", 0.1, 3.0, 1.0, 0.1)


    # Ensure the generated_files list persists across reruns
    if "generated_files" not in st.session_state:
        st.session_state.generated_files = []

    # 点击生成按钮
    if st.button("生成音频"):
        # 删除生成的音频文件
        for file in st.session_state.generated_files:
            if os.path.exists(file):
                os.remove(file)
        generated_files = []
        st.session_state.generated_files.clear()
        # 调用文本转语音函数并生成音频
        generated_files = sync_VolceTextToSpeech(text, voices, voice_emotion,rate, volume, pitch)
        st.session_state.generated_files.extend(generated_files)

    # 显示已生成的音频文件列表和下载按钮
    if st.session_state.generated_files:
        for file in st.session_state.generated_files:
            if os.path.exists(file):
                filename = os.path.basename(file)
                st.text(f"音频文件: {filename}")  # 显示文件名作为标题
                with open(file, "rb") as filedata:
                    btn = st.download_button(
                        label="下载文件",
                        data=filedata,
                        file_name=filename,
                        mime="mp3"
                    )
                st.audio(file,format='audio/mpeg')

    # 清除音频和文本
    if st.button("清除"):
        # 删除生成的音频文件
        for file in st.session_state.generated_files:
            if os.path.exists(file):
                os.remove(file)
        generated_files = []
        st.session_state.generated_files.clear()
        st.rerun()
