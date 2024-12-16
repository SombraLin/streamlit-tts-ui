import streamlit as st
import edge_tts
import asyncio
import os
import json
import volce_tts_stream

# 全局变量存储生成的音频文件列表
generated_files = []

def render_edge_tts_ui():
    # Ensure the generated_files list persists across reruns
    if "generated_files" not in st.session_state:
        st.session_state.generated_files = []
     # 删除生成的音频文件
    for file in st.session_state.generated_files:
        if os.path.exists(file):
            os.remove(file)
    st.session_state.generated_files.clear()
    # 加载语音数据
    with open("voice_short.txt", "r", encoding="utf-8") as f:
        voice_data = json.load(f)

    # Create a dictionary of supported voices
    SUPPORTED_VOICES = {
        f"{voice['Gender']}-{voice['ShortNameCN']}": voice['ShortNameCN']
        for voice in voice_data
    }

    # Create a dictionary of supported voices
    VOICER_LIST = {
        f"{voice['Gender']}-{voice['ShortNameCN']}": voice['Voicer']
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
    async def EdgeTextToSpeech(text, voices, rate, volume):
        audio_file_paths=[]
        voices = VOICER_LIST[voices]
        print(f'发音人:{voices}')
        # 生成文件名：取每段文本前16个字符
        prefix = text[:64].encode('utf-8')[:64].decode('utf-8', errors='ignore')
        # 替换特殊字符
        output_file = ''.join(c for c in prefix if c.isalnum())
        output_file +=".mp3"
        if (rate >= 0):
            rates = rate = "+" + str(rate) + "%"
        else:
            rates = str(rate) + "%"
        if (volume >= 0):
            volumes = "+" + str(volume) + "%"
        else:
            volumes = str(volume) + "%"
        communicate = edge_tts.Communicate(text,
                                        voices,
                                        rate=rates,
                                        volume=volumes,
                                        proxy=None)
        await communicate.save(output_file)
        audio_file = os.path.join(os.path.dirname(__file__), output_file)
        if (os.path.exists(audio_file)):
            audio_file_paths.append(audio_file)
            return audio_file_paths
        else:
            return []

    # 同步执行异步文本转语音函数
    def sync_EdgeTextToSpeech(text, voices, rate, volume):
        return asyncio.run(EdgeTextToSpeech(text, voices, rate, volume))

    # Streamlit App
    st.title("微软Edge TTS语音合成")

    # 输入文本
    text = st.text_area("输入文本", height=400)

    # 选择发音人
    voices = st.selectbox("选择发音人", list(SUPPORTED_VOICES.keys()), index=0)

    # 选择情感
    #voice_emotion = st.selectbox("选择情感", list(SUPPORTED_EMOTIONS.values()), index=0)

    # 选择语速
    rate = st.slider("语速增减", -100, 100, 0, 10)

    # 选择音量
    volume = st.slider("音量增减",  -100, 100, 0, 10)


    # 点击生成按钮
    if st.button("生成音频"):
        # 调用文本转语音函数并生成音频
        # 删除生成的音频文件
        for file in st.session_state.generated_files:
            if os.path.exists(file):
                os.remove(file)
        generated_files = []
        st.session_state.generated_files.clear()
        generated_files = sync_EdgeTextToSpeech(text, voices, rate, volume)
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
