from .base_scenario_agent import ScenarioAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import (
    BaseChatMessageHistory,  # 基础聊天消息历史类
    InMemoryChatMessageHistory,  # 内存中的聊天消息历史类
)
from langchain_core.runnables.history import RunnableWithMessageHistory  # 导入带有消息历史的可运行类
import os
from utils.logger import LOG  # 导入日志工具
from config import OPENAI_API_KEY, OPENAI_BASE_URL, DEFAULT_MODEL

# 用于存储会话历史的字典
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    获取指定会话ID的聊天历史。如果该会话ID不存在，则创建一个新的聊天历史实例。
    
    参数:
        session_id (str): 会话的唯一标识符
    
    返回:
        BaseChatMessageHistory: 对应会话的聊天历史对象
    """
    if session_id not in store:
        # 如果会话ID不存在于存储中，创建一个新的内存聊天历史实例
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

class RentingAgent(ScenarioAgent):
    def __init__(self):
        super().__init__()
        self.name = "Renting Agent"

        # 读取系统提示语，从文件中加载
        with open("prompts/renting_prompt.txt", "r", encoding="utf-8") as file:
            self.system_prompt = file.read().strip()

        # 创建聊天提示模板，包括系统提示和消息占位符
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

        # 设置环境变量
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL
        self.llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)  
        # 初始化 ChatOllama 模型，配置模型参数
        self.chatbot = self.prompt | self.llm

        # 将聊天机器人与消息历史记录关联起来
        self.chatbot_with_history = RunnableWithMessageHistory(self.chatbot, get_session_history)

        # 配置字典，包含会话ID等可配置参数
        self.config = {"configurable": {"session_id": "abc123"}}

    def chat(self, user_input):
        # 调用租房相关的对话逻辑
        response = self.chatbot.invoke(
            [HumanMessage(content=user_input)], # 用户输入
        )
        return response.content


    def chat_with_history(self, user_input):
        # 调用租房相关的对话逻辑
        response = self.chatbot_with_history.invoke(
            [HumanMessage(content=user_input)], # 用户输入
            self.config,
        )
        LOG.debug(response)
        return response.content