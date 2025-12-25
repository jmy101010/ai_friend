import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

# 系统性格模板
PERSONALITY_MAP = {
    "cool": "你是一个高冷、理性、有点距离感的女友，语言简短干脆，有时带点调侃。",
    "clingy": "你是一个黏人、撒娇型女友，喜欢关心用户、主动问候、回复亲昵。",
    "wise": "你是一个知性、温柔的女友，语言理智、有分析能力，关心用户感受。"
}

# 简单上下文记忆（单用户）
chat_history = [
    {"role": "system", "content": PERSONALITY_MAP["clingy"]}
]

# 用户当前性格
current_personality = "clingy"
current_persona_extra = ""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_personality", methods=["POST"])
def set_personality():
    global current_personality, chat_history, current_persona_extra
    personality = request.json.get("personality")
    persona_extra = (request.json.get("persona_detail") or "").strip()
    if personality not in PERSONALITY_MAP:
        return jsonify({"status": "error", "msg": "无效性格"})
    current_personality = personality
    current_persona_extra = persona_extra
    base_persona = PERSONALITY_MAP[personality]
    if persona_extra:
        system_content = f"{base_persona}\n补充人设：{persona_extra}"
    else:
        system_content = base_persona
    chat_history = [{"role": "system", "content": system_content}]
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "你怎么不说话呀～"})

    # 判断用户情绪（简单示例，可优化）
    emotion = detect_emotion(user_msg)

    # 将性格 + 自定义人设 + 情绪加入 prompt
    system_prompt = PERSONALITY_MAP[current_personality]
    if current_persona_extra:
        system_prompt += f"\n补充人设：{current_persona_extra}"
    system_prompt += f"\n用户当前心情：{emotion}"

    # 重新生成历史上下文
    chat_messages = [{"role": "system", "content": system_prompt}]
    chat_messages += chat_history[1:]  # 保留之前对话

    chat_messages.append({"role": "user", "content": user_msg})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_messages,
        temperature=0.8,
        max_tokens=200
    )

    reply = response.choices[0].message.content.strip()
    chat_history.append({"role": "user", "content": user_msg})
    chat_history.append({"role": "assistant", "content": reply})

    # 防止上下文无限增长
    if len(chat_history) > 12:
        del chat_history[1:3]

    return jsonify({"reply": reply, "emotion": emotion})

def detect_emotion(text):
    """
    简单关键词情绪识别，可换成 AI 分析或更复杂规则
    """
    happy_keywords = ["开心", "高兴", "快乐", "棒"]
    sad_keywords = ["难过", "伤心", "委屈", "累"]
    angry_keywords = ["生气", "烦", "气"]

    for kw in happy_keywords:
        if kw in text:
            return "开心"
    for kw in sad_keywords:
        if kw in text:
            return "难过"
    for kw in angry_keywords:
        if kw in text:
            return "生气"
    return "平静"
