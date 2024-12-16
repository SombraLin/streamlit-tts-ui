#coding=utf-8

'''
requires Python 3.6 or later

pip install asyncio
pip install websockets

'''
import os
import re
import asyncio
import websockets
import uuid
import json
import gzip
import copy
from datetime import datetime
MESSAGE_TYPES = {11: "audio-only server response", 12: "frontend server response", 15: "error message from server"}
MESSAGE_TYPE_SPECIFIC_FLAGS = {0: "no sequence number", 1: "sequence number > 0",
                               2: "last message from server (seq < 0)", 3: "sequence number < 0"}
MESSAGE_SERIALIZATION_METHODS = {0: "no serialization", 1: "JSON", 15: "custom type"}
MESSAGE_COMPRESSIONS = {0: "no compression", 1: "gzip", 15: "custom compression method"}

appid = "2388566183"
token = "g5btTyzAuse5mywyjZR8jvVYzyaL-6oQ"
cluster = "volcano_tts"
voice_type = "BV701_streaming"
emotion = "happy"
host = "openspeech.bytedance.com"
api_url = f"wss://{host}/api/v1/tts/ws_binary"
#
# happy
# sad
# angry
# scare
# hate
# surprise
# tear
# novel_dialog
# narrator
# narrator_immersive
#
# version: b0001 (4 bits)
# header size: b0001 (4 bits)
# message type: b0001 (Full client request) (4bits)
# message type specific flags: b0000 (none) (4bits)
# message serialization method: b0001 (JSON) (4 bits)
# message compression: b0001 (gzip) (4bits)
# reserved data: 0x00 (1 byte)
default_header = bytearray(b'\x11\x10\x11\x00')

request_json = {
    "app": {
        "appid": appid,
        "token": "access_token",
        "cluster": cluster
    },
    "user": {
        "uid": "388808087185088"
    },
    "audio": {
        "voice_type": "xxx",
        "emotion":"happy",
        "encoding": "mp3",
        "rate":24000,
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": "xxx",
        "text": "字节跳动语音合成。",
        "text_type": "ssml",
        "operation": "xxx"
    }
}

async def tts_stream(text,wsChunk,rate=24000,voice_type="BV701_streaming",emotion="happy",speed=1, volume=1,pitch=1,filename="tts_stream.pcm"):
    submit_request_json = copy.deepcopy(request_json)
    submit_request_json["audio"]["voice_type"] = voice_type
    submit_request_json["request"]["reqid"] = str(uuid.uuid4())
    submit_request_json["request"]["operation"] = "submit"
    submit_request_json["request"]["text"] = text
    submit_request_json["audio"]["rate"] = rate
    submit_request_json["audio"]["speed_ratio"] = speed
    submit_request_json["audio"]["volume_ratio"] = volume
    submit_request_json["audio"]["pitch_ratio"] = pitch
    submit_request_json["audio"]["emotion"] = emotion

    payload_bytes = str.encode(json.dumps(submit_request_json))
    payload_bytes = gzip.compress(payload_bytes)  # if no compression, comment this line
    full_client_request = bytearray(default_header)
    full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))  # payload size(4 bytes)
    full_client_request.extend(payload_bytes)  # payload
    # print("\n------------------------ test 'submit' -------------------------")
    print("request json: ", submit_request_json)
    print("\nrequest bytes: ", full_client_request)

    file_to_save = open(filename, "wb")
    header = {"Authorization": f"Bearer; {token}"}
    async with websockets.connect(api_url, extra_headers=header, ping_interval=None) as ws:
        await ws.send(full_client_request)
        while True:
            res = await ws.recv()
            done,message_type,audio_buf = parse_response(res)
            if message_type == 0xb:
                if done:
                    file_to_save.write(audio_buf)
                    file_to_save.close()
                    for i in range(0, len(audio_buf), wsChunk):
                        chunk = audio_buf[i:i+wsChunk]
                        yield {'type': 0xb, 'status': 2, 'audio': chunk}
                    break
                else:
                    file_to_save.write(audio_buf)
                    for i in range(0, len(audio_buf), wsChunk):
                        chunk = audio_buf[i:i+wsChunk]
                        yield {'type': 0xb, 'status': 1, 'audio': chunk}
            elif message_type == 0xf:
                    yield {'type':0xf,'status':2,'audio':b''}
                    break
        print("\nclosing the connection...")


def parse_response(res):
    # print("--------------------------- response ---------------------------")
    # print(f"response raw bytes: {res}")
    protocol_version = res[0] >> 4
    header_size = res[0] & 0x0f
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0f
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0f
    reserved = res[3]
    header_extensions = res[4:header_size*4]
    payload = res[header_size*4:]
    # print(f"            Protocol version: {protocol_version:#x} - version {protocol_version}")
    # print(f"                 Header size: {header_size:#x} - {header_size * 4} bytes ")
    # print(f"                Message type: {message_type:#x} - {MESSAGE_TYPES[message_type]}")
    # print(f" Message type specific flags: {message_type_specific_flags:#x} - {MESSAGE_TYPE_SPECIFIC_FLAGS[message_type_specific_flags]}")
    # print(f"Message serialization method: {serialization_method:#x} - {MESSAGE_SERIALIZATION_METHODS[serialization_method]}")
    # print(f"         Message compression: {message_compression:#x} - {MESSAGE_COMPRESSIONS[message_compression]}")
    # print(f"                    Reserved: {reserved:#04x}")
    if header_size != 1:
        print(f"           Header extensions: {header_extensions}")
    if message_type == 0xb:  # audio-only server response
        if message_type_specific_flags == 0:  # no sequence number as ACK
            print("                Payload size: 0")
            return False,0xb,b''
        else:
            sequence_number = int.from_bytes(payload[:4], "big", signed=True)
            payload_size = int.from_bytes(payload[4:8], "big", signed=False)
            payload = payload[8:]
            # print(f"             Sequence number: {sequence_number}")
            # print(f"                Payload size: {payload_size} bytes")
        # file.write(payload)
        if sequence_number < 0:
            return True,message_type,payload
            # return True
        else:
            return False,message_type,payload
            # return False
    elif message_type == 0xf:
        code = int.from_bytes(payload[:4], "big", signed=False)
        msg_size = int.from_bytes(payload[4:8], "big", signed=False)
        error_msg = payload[8:]
        if message_compression == 1:
            error_msg = gzip.decompress(error_msg)
        error_msg = str(error_msg, "utf-8")
        print(f"          Error message code: {code}")
        print(f"          Error message size: {msg_size} bytes")
        print(f"               Error message: {error_msg}")
        return True,message_type,payload
    elif message_type == 0xc:
        msg_size = int.from_bytes(payload[:4], "big", signed=False)
        payload = payload[4:]
        if message_compression == 1:
            payload = gzip.decompress(payload)
        print(f"            Frontend message: {payload}")
    else:
        print("undefined message type!")
        return True,message_type,payload

def split_text_by_punctuation(text, max_length):
    """ 按标点符号分割文本，确保每段的长度不超过max_length，并以标点符号结尾 """
    # 匹配中文和英文的标点符号
    punctuations = re.compile(r'[。.！？?,，]')
    
    start = 0
    chunks = []
    while start < len(text):
        # 预先截取最大长度的子串
        end = min(start + max_length, len(text))
        sub_text = text[start:end]

        # 处理可能截断的尖括号标签
        if '<' in sub_text and '>' not in sub_text:
            # 向前扩展，找到完整的标签
            end = text.find('>', end) + 1
            sub_text = text[start:end]

        # 查找最后一个标点符号的位置
        match = punctuations.search(sub_text[::-1])  # 从结尾向前查找标点符号
        if match:
            punct_pos = end - match.start() - 1
            chunks.append(text[start:punct_pos + 1])
            start = punct_pos + 1
        else:
            # 如果未找到标点符号，直接使用最大长度的子串
            chunks.append(sub_text)
            start = end
    
    return chunks
async def text_split_test():
    # 获取用户输入的txt文件名
    file_name = input("请输入txt文件名: ")
    
    # 读取文件内容
    if not os.path.exists(file_name):
        print("文件不存在，请检查文件名。")
        return
    
    with open(file_name, 'r', encoding='utf-8') as f:
        text = f.read()


    # 确保文本长度最大为1000字节，且以标点符号结尾
    max_length = 300
    chunks = split_text_by_punctuation(text, max_length)
    for i, chunk in enumerate(chunks):
        print(f'{i}:\n{chunk}\n')

async def main():
    # 获取用户输入的txt文件名
    file_name = input("请输入txt文件名: ")
    
    # 读取文件内容
    if not os.path.exists(file_name):
        print("文件不存在，请检查文件名。")
        return
    
    with open(file_name, 'r', encoding='utf-8') as f:
        text = f.read()


    # 确保文本长度最大为1000字节，且以标点符号结尾
    max_length = 300
    chunks = split_text_by_punctuation(text, max_length)
    
    # 创建情绪选项字典，默认为 'happy'
    emotions = {
        1: "happy - 开心",
        2: "sad - 悲伤",
        3: "angry - 生气",
        4: "scare - 害怕",
        5: "hate - 憎恨",
        6: "surprise - 惊讶",
        7: "tear - 流泪",
        8: "novel_dialog - 小说对话",
        9: "narrator - 叙述者",
        10: "narrator_immersive - 沉浸式叙述者"
    }
    emotion_values = {
        1: "happy",
        2: "sad",
        3: "angry",
        4: "scare",
        5: "hate",
        6: "surprise",
        7: "tear",
        8: "novel_dialog",
        9: "narrator",
        10: "narrator_immersive"
    }

    # 展示选项给用户
    print("请选择情绪:")
    for key, value in emotions.items():
        print(f"{key}. {value}")

    # 获取用户输入，默认为 'happy'
    choice = input("请输入编号 (默认为 1): ")
    emotion_selected = emotion_values.get(int(choice), "happy")

    # 输出选择的情绪
    print(f"你选择的情绪是: {emotion_selected}")

    # 生成文件名：取每段文本前16个字符
    prefix = text[:64].encode('utf-8')[:64].decode('utf-8', errors='ignore')
    # 替换特殊字符
    prefix = ''.join(c for c in prefix if c.isalnum())

    # 遍历每个分段进行处理
    for i, chunk in enumerate(chunks):
        # 处理文本，添加<speak>标签
        chunk = "<speak>" + chunk + "</speak>"

        # 生成文件名
        filename = f"tts_{prefix}_{i+1}.mp3"

        # 异步调用tts_stream函数
        async for result in tts_stream(chunk, 4096, 24000,"BV701_streaming",emotion_selected,1,1,1, filename):
            print('.')
        print(f'文件已生成：{filename}')

async def volce_tts(text,voicer,emotion,rate, volume,pitch,filename):
    # 确保文本长度最大为1000字节，且以标点符号结尾
    max_length = 300
    text +="。"
    chunks = split_text_by_punctuation(text, max_length)
    # 生成文件名：取每段文本前16个字符
    prefix = text[:64].encode('utf-8')[:64].decode('utf-8', errors='ignore')
    # 替换特殊字符
    prefix = ''.join(c for c in prefix if c.isalnum())
    # 用于保存生成的音频文件路径
    audio_file_paths = []
    # 遍历每个分段进行处理
    for i, chunk in enumerate(chunks):
        # 处理文本，添加<speak>标签
        chunk = "<speak>" + chunk + "</speak>"
        # 生成文件名
        filename = f"{prefix}{i+1}.mp3"
        async for result in tts_stream(chunk, 4096, 24000,voicer, emotion, rate, volume,pitch, filename):
            print('.')
        print(f'文件已生成：{filename}')
        # filename = os.path.join(os.path.dirname(__file__), filename)
        audio_file_paths.append(filename)
    return audio_file_paths
    
if __name__ == '__main__':
    # asyncio.run(main())
    asyncio.run(text_split_test())
