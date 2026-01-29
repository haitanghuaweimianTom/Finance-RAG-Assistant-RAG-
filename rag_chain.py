import chromadb
from openai import OpenAI
import requests
import json
import os
from dotenv import load_dotenv

# 自动从当前目录的 .env 文件加载环境变量
load_dotenv()

# 修改配置行
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")


SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5" 
#改为硅基流动存在的模型名
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"  
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "finance_reports"

# 初始化
openai_client = OpenAI(api_key=SILICONFLOW_API_KEY, base_url=SILICONFLOW_BASE_URL)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# 获取 Collection（增加报错处理）
try:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
except Exception as e:
    print(f"警告：无法加载向量库 {COLLECTION_NAME}，请确保已运行存入数据的脚本。错误: {e}")

def retrieve_relevant_chunks(query, top_k=5):
    """ 第一步：检索 """
    # 修复：确保调用的是字符串模型名
    resp = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query]
    )
    query_embedding = resp.data[0].embedding
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results["documents"][0] if results["documents"] else []

def rerank_chunks(query, docs, top_n=3):
    """ 第二步：标准的硅基流动 Rerank 调用方式 """
    if not docs: return []
    
    url = f"{SILICONFLOW_BASE_URL}/rerank"
    payload = {
        "model": RERANK_MODEL,
        "query": query,
        "documents": docs,
        "top_n": top_n,
        "return_documents": True
    }
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        # 提取重排后的文档内容
        return [item['document']['text'] if isinstance(item['document'], dict) else item['document'] for item in result['results']]
    else:
        print(f"Rerank 失败: {response.text}")
        return docs[:top_n] # 失败则退回到普通检索结果

def build_prompt(query, relevant_docs):
    """ 第三步：构造 Prompt """
    context = "\n\n".join([f"【资料{i+1}】: {doc}" for i, doc in enumerate(relevant_docs)])
    prompt = f"""你是一位专业的金融分析师。请基于以下研报片段回答问题。
若资料不足，请直说。

资料库：
{context}

问题：{query}
回答："""
    return prompt

def call_llm(prompt):
    """ 第四步：LLM 生成 """
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

def rag_qa_pipeline(user_query):
    try:
        print(f"正在处理提问: {user_query}")
        # 1. 检索
        raw_docs = retrieve_relevant_chunks(user_query)
        # 2. 重排 (Rerank)
        top_docs = rerank_chunks(user_query, raw_docs)
        # 3. 构造 Prompt
        prompt = build_prompt(user_query, top_docs)
        # 4. 生成
        return call_llm(prompt)
    except Exception as e:
        return f"流程出错：{str(e)}"

if __name__ == "__main__":
    print("="*30)
    print("金融研报智能助手已启动")
    print("输入 'exit' 或 'quit' 退出程序")
    print("="*30)

    while True:
        # 获取用户自定义输入
        user_query = input("\n请输入您的金融问题 > ").strip()

        # 处理退出逻辑
        if user_query.lower() in ['exit', 'quit', '退出']:
            print("程序已退出。")
            break

        # 处理空输入
        if not user_query:
            print("问题不能为空，请重新输入。")
            continue

        # 执行 RAG 流程
        print("正在检索并分析中，请稍候...")
        answer = rag_qa_pipeline(user_query)

        # 打印结果
        print("\n" + "-"*20 + " 分析结果 " + "-"*20)
        print(answer)
        print("-"*50)