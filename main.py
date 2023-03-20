# 导入所需的库
import json
import subprocess
import traceback
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import openai
import pygame
from bilibili_api import live, sync

# 读取配置文件信息
with open("config.json", "r", encoding='utf-8') as jsonfile:
    config_data = json.load(jsonfile)

# 设置会话初始值
session_config = {'msg': [{"role": "system", "content": config_data['chatgpt']['preset']}]}
sessions = {}
current_key_index = 0

# 配置 OpenAI API 和 Bilibili 直播间 ID
openai.api_base = config_data["api"]  # https://chat-gpt.aurorax.cloud/v1 https://api.openai.com/v1
room_id = config_data["room_display_id"]

# 初始化 Bilibili 直播间和 TTS 语音
room = live.LiveDanmaku(room_id)
tts_voice = config_data["tts_voice"]


def chat(msg, sessionid):
    """
    ChatGPT 对话函数
    :param msg: 用户输入的消息
    :param sessionid: 当前会话 ID
    :return: ChatGPT 返回的回复内容
    """
    try:
        # 获取当前会话
        session = get_chat_session(sessionid)

        # 将用户输入的消息添加到会话中
        session['msg'].append({"role": "user", "content": msg})

        # 添加当前时间到会话中
        session['msg'][1] = {"role": "system", "content": "current time is:" + get_bj_time()}

        # 调用 ChatGPT 接口生成回复消息
        message = chat_with_gpt(session['msg'])

        # 如果返回的消息包含最大上下文长度限制，则删除超长上下文并重试
        if message.__contains__("This model's maximum context length is 4096 token"):
            del session['msg'][2:3]
            del session['msg'][len(session['msg']) - 1:len(session['msg'])]
            message = chat(msg, sessionid)

        # 将 ChatGPT 返回的回复消息添加到会话中
        session['msg'].append({"role": "assistant", "content": message})

        # 输出会话 ID 和 ChatGPT 返回的回复消息
        print("会话ID: " + str(sessionid))
        print("ChatGPT返回内容: ")
        print(message)

        # 返回 ChatGPT 返回的回复消息
        return message

    # 捕获异常并打印堆栈跟踪信息
    except Exception as error:
        traceback.print_exc()
        return str('异常: ' + str(error))


def get_bj_time():
    """
    获取北京时间
    :return: 当前北京时间，格式为 '%Y-%m-%d %H:%M:%S'
    """
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)  # 获取当前 UTC 时间
    SHA_TZ = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai',
    )
    beijing_now = utc_now.astimezone(SHA_TZ)  # 将 UTC 时间转换为北京时间
    fmt = '%Y-%m-%d %H:%M:%S'
    now_fmt = beijing_now.strftime(fmt)
    return now_fmt


def get_chat_session(sessionid):
    """
    获取指定 ID 的会话，如果不存在则创建一个新的会话
    :param sessionid: 会话 ID
    :return: 指定 ID 的会话
    """
    sessionid = str(sessionid)
    if sessionid not in sessions:
        config = deepcopy(session_config)
        config['id'] = sessionid
        config['msg'].append({"role": "system", "content": "current time is:" + get_bj_time()})
        sessions[sessionid] = config
    return sessions[sessionid]


def chat_with_gpt(messages):
    """
    使用 ChatGPT 接口生成回复消息
    :param messages: 上下文消息列表
    :return: ChatGPT 返回的回复消息
    """
    global current_key_index
    max_length = len(config_data['openai']['api_key']) - 1

    try:
        if not config_data['openai']['api_key']:
            return "请设置Api Key"
        else:
            # 判断是否所有 API key 均已达到速率限制
            if current_key_index > max_length:
                current_key_index = 0
                return "全部Key均已达到速率限制,请等待一分钟后再尝试"
            openai.api_key = config_data['openai']['api_key'][current_key_index]

        # 调用 ChatGPT 接口生成回复消息
        resp = openai.ChatCompletion.create(
            model=config_data['chatgpt']['model'],
            messages=messages
        )
        resp = resp['choices'][0]['message']['content']

    # 处理 OpenAIError 异常
    except openai.OpenAIError as e:
        if str(e).__contains__("Rate limit reached for default-gpt-3.5-turbo") and current_key_index <= max_length:
            current_key_index = current_key_index + 1
            print("速率限制，尝试切换key")
            return chat_with_gpt(messages)
        elif str(e).__contains__(
                "Your access was terminated due to violation of our policies") and current_key_index <= max_length:
            print("请及时确认该Key: " + str(openai.api_key) + " 是否正常，若异常，请移除")

            # 判断是否所有 API key 均已尝试
            if current_key_index + 1 > max_length:
                return str(e)
            else:
                print("访问被阻止，尝试切换Key")
                current_key_index = current_key_index + 1
                return chat_with_gpt(messages)
        else:
            print('openai 接口报错: ' + str(e))
            resp = "openai 接口报错: " + str(e)

    return resp


@room.on('DANMU_MSG')
async def on_danmaku(event):
    """
    处理直播间弹幕事件
    :param event: 弹幕事件数据
    """
    content = event["data"]["info"][1]  # 获取弹幕内容
    user_name = event["data"]["info"][2][1]  # 获取发送弹幕的用户昵称

    # 判断弹幕是否以句号或问号结尾，如果是则进行回复
    if content.endswith("。") or content.endswith("？") or content.endswith("?"):
        # 获取当前用户的会话
        session = get_chat_session(str(user_name))

        # 输出当前用户发送的弹幕消息
        print(f"[{user_name}]: {content}")

        # 调用 ChatGPT 接口生成回复消息
        prompt = f"{content}"
        response = chat(prompt, session)

        # 输出 ChatGPT 返回的回复消息
        print(f"[AI回复{user_name}]：{response}")

        # 使用 Edge TTS 生成回复消息的语音文件
        cmd = f'edge-tts --voice {tts_voice} --text "{content}{response}" --write-media output.mp3'
        subprocess.run(cmd, shell=True)

        # 将 AI 回复记录到日志文件中
        with open("./log.txt", "a", encoding="utf-8") as f:
            f.write(f"[AI回复{user_name}]：{response}\n")

        # 播放生成的语音文件
        pygame.mixer.init()
        pygame.mixer.music.load('output.mp3')

        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()


# 启动 Bilibili 直播间连接
sync(room.connect())
