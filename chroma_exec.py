from DocumentExtract import extract_text_from_pdf
from VectorDbOperate import MyVectorDBConnector
from openai import OpenAI
from RAG import RAG_Bot
from dotenv import load_dotenv, find_dotenv
import os

# 读取环境变量
_ = load_dotenv(find_dotenv())  # 读取本地 .env 文件，里面定义了 OPENAI_API_KEY
# 创建OpenAI客户端
client = OpenAI()

text_model = "text-embedding-3-small"
llm_model = "gpt-4o-mini"

# 定义API -> 生成向量 text-embedding-ada-002 text-embedding-3-small
def get_embeddings(texts, model=text_model):
    """封装 OpenAI 的 Embedding 模型接口"""
    data = client.embeddings.create(input=texts, model=model).data
    return [x.embedding for x in data]

# 定义API -> 获取OpenAI会话响应
def get_completion(prompt, model=llm_model):
    """封装 openai 接口 获取会话响应"""
    data = list()  # 构建当前对话
    data.append({
        "role": "system",
        "content": """你是一个问答机器人。
    你的任务是根据下述给定的已知信息回答用户问题，并且用中文回答用户问题。
    确保你的回复完全依据下述已知信息。不要编造答案。
    如果下述已知信息不足以回答用户的问题，请直接回复"在提供的文档中找不到相关信息，我无法回答您的问题"。"""
    })
    data.append({
        "role": "user",
        "content": prompt
    })

    response = client.chat.completions.create(
        model=model,
        messages=data,
        temperature=0,  # 模型输出的随机性，0 表示随机性最小
        stream=True
    )
    return response

def run_rag(filePath: str, dialogId: str, userQuery: str):
    """
    rag主函数
    filePath 文档路径
    dialogId 对话ID
    userQuery 检索的问题
    """
    # 创建一个向量数据库对象
    vector_db = MyVectorDBConnector(dialogId, get_embeddings, host_ip=os.getenv("CHROMA_HOST"),
                                    host_port=os.getenv("CHROMA_PORT"))
    # 如果是第一次对话，向向量数据库中添加文档
    if filePath != "None":
        # 提取文档段落，构建段落列表
        paragraphs: list[str] = extract_text_from_pdf(filePath, min_line_length=10)
        # 向向量数据库中添加文档
        vector_db.add_documents(paragraphs)

    # 创建一个RAG机器人
    bot = RAG_Bot(
        vector_db,
        llm_api=get_completion
    )

    # 获取RAG应答
    response = bot.chat_(userQuery)

    # 流式读取响应结果
    resTxt = ""
    for msg in response:
        if len(msg.choices) != 0:
            delta = msg.choices[0].delta
            if delta.content:
                text_delta = delta.content
                resTxt = resTxt + text_delta
    resTxt = "RAG: " + resTxt.strip()

    if resTxt == "RAG: ":
        resTxt = "Error: 系统异常"
    if resTxt.startswith("RAG: 在提供的文档中找不到相关信息，我无法回答您的问题"):
        # 从大模型的知识库中查找信息
        resTxt = ""
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个问答机器人。请根据用户的问题进行回答，不要输出与问题无关的信息。如果找不到问题对应的答案，不要编造答案，请输出：我未学习相关内容，无法回答您的问题。"
                },
                {
                    "role": "user",
                    "content": userQuery
                }
            ],
            temperature=0,  # 模型输出的随机性，0 表示随机性最小
            stream=True
        )
        for msg in response:
            if len(msg.choices) != 0:
                delta = msg.choices[0].delta
                if delta.content:
                    text_delta = delta.content
                    resTxt = resTxt + text_delta
        resTxt = "LLM: " + resTxt.strip()

    # 构建用于存储的对话记录
    messages = list()

    # 将应答内容加入对话记录
    messages.append(
        {
            "role": "user",
            "content": userQuery
        }
    )
    messages.append(
        {
            "role": "assistant",
            "content": resTxt
        }
    )

    # 返回会话记录
    return messages