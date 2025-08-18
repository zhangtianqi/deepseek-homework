from langchain.embeddings.base import Embeddings
import requests
import json
import time
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.lkeap.v20240522 import lkeap_client, models

import os
import types

class TencentLKEEmbeddings(Embeddings):
    def __init__(self, secret_id, secret_key, region="ap-guangzhou"):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.endpoint = "lkeap.tencentcloudapi.com"
        self.model = "lke-text-embedding-v1"  # 腾讯云嵌入模型
        self.dimension = 1024  # 腾讯云LKE的向量维度

    def _get_embedding(self, text: str) -> list:
        """调用腾讯云GetEmbedding接口"""
        try:
            cred = credential.Credential(self.secret_id, self.secret_key)
            http_profile = HttpProfile(endpoint=self.endpoint)
            client_profile = ClientProfile(httpProfile=http_profile)
            client = lkeap_client.LkeapClient(cred, self.region, client_profile)
            req = models.GetEmbeddingRequest()
            req.Model = self.model
            req.Inputs = [text]  # 单次支持多文本，此处简化
            resp = client.GetEmbedding(req)
            return resp.Data[0].Embedding  # 返回首个文本的向量
        except TencentCloudSDKException as e:
            raise ValueError(f"API调用失败: {e}")

    def embed_documents(self, texts: list) -> list:
        """批量生成文档向量"""
        return [self._get_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list:
        """生成查询向量"""
        return self._get_embedding(text)

# from langchain_chroma import Chroma
# from langchain_core.documents import Document

# # 1. 准备文档数据
# documents = [
#     Document(page_content="腾讯云是领先的云计算服务商"),
#     Document(page_content="LKEAP提供大模型知识引擎服务")
# ]

# # 2. 初始化自定义嵌入对象
# embeddings = TencentLKEEmbeddings(
#     secret_id="",  # 腾讯云API密钥
#     secret_key=""
# )

# #resp = embeddings.embed_query("苹果")
# #print(resp)

# # 3. 创建Chroma向量库
# #vectorstore = Chroma.from_documents(
# #    documents=documents,
# #    embedding=embeddings,        # 注入腾讯云嵌入服务
# #    persist_directory="./tencent_db"  # 持久化路径
# #)

# vectorstore = Chroma.from_documents(
#     documents=documents,
#     embedding=embeddings,        # 注入腾讯云嵌入服务
#     persist_directory="./tencent_db"
# )
