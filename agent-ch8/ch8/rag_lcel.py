from real_vector_store import TencentIMVectorDatabase
from tencent_embeddings import TencentLKEEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os

# 设置DeepSeek API
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com"

# 构建向量数据库
# db_manager = TencentIMVectorDatabase(
#             secret_id="",
#             secret_key="",
#             db_name="tencent.im.db"
#         )
# db_manager.create_database_from_markdown(
#     markdown_file="/Users/zhangtianqi/git_root/agent_homework/ch8/腾讯云IM群组系统完整文档.md",
#     batch_size=3
# )


# 构建embedings对象及向量数据库
embeddings = TencentLKEEmbeddings(
    secret_id="",  # 腾讯云API密钥
    secret_key="",
    region="ap-guangzhou"
)

vectorstore = Chroma(
    embedding_function=embeddings,        # 注入腾讯云嵌入服务
    persist_directory="./tencent.im.db"
)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
type(retriever)

# retriever_docs = retriever.invoke("不同群组的限制差异是什么？")
# print(retriever_docs)

llm = ChatOpenAI(model="deepseek-chat")

prompt = ChatPromptTemplate.from_template('''You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question} \n Context: {context} \n Answer:''')


prompt_v2 = ChatPromptTemplate.from_template('''你是腾讯云即时通信IM的专业技术助手。请基于提供的文档内容回答用户问题。

# 回答要求：
# 1. 基于提供的文档内容回答，不要编造信息
# 2. 如果文档中没有相关信息，请明确说明
# 3. 回答要结构化、专业、准确
# 4. 使用表格、列表等格式提高可读性
# 5. 重点信息用**粗体**标注

# 文档内容：
# {context}

基于上述腾讯云IM文档内容，请回答以下问题：
# {question}''')

# 定义格式化文档的函数
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

questions = [
    "不同群组的限制差异是什么？",
    "不同群组消息能力的差异是什么？",
    "群资料有哪些字段？"
]

for question in questions:
    result = rag_chain.invoke(question)
    print(f"Question: {question}\nAnswer: {result}\n")

print("----------------rag_chain_v2----------------")

rag_chain_v2 = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt_v2
    | llm
    | StrOutputParser()
)

for question in questions:
    result = rag_chain_v2.invoke(question)
    print(f"Question: {question}\nAnswer: {result}\n")




