import os
import chromadb
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import hashlib  # 新增导入
# 自动从当前目录的 .env 文件加载环境变量
load_dotenv()

# 修改配置行
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNK_FILE_PATH = "./chunks/all_finance_chunks.txt"  # 对应 data_process.py 生成的总Chunk文件（项目根目录下）
CHROMA_DB_PATH = "./chroma_db"  # 向量库存放目录（项目根目录下）
COLLECTION_NAME = "finance_reports"

# 初始化客户端
def init_clients():
    """初始化硅基流动客户端和ChromaDB客户端"""
    # 硅基流动OpenAI兼容客户端
    openai_client = OpenAI(
        api_key=SILICONFLOW_API_KEY,
        base_url=SILICONFLOW_BASE_URL
    )
    
    # ChromaDB持久化客户端
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    # 获取或创建集合
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "金融研报向量数据库"}
    )
    
    return openai_client, collection

def load_chunks_from_file(chunk_file_path):
    """
    从总Chunk文件中读取所有有效片段（过滤分割线和空内容）
    """
    if not os.path.exists(chunk_file_path):
        raise FileNotFoundError(f"Chunk文件 {chunk_file_path} 不存在，请先运行 data_process.py")
    
    chunks = []
    with open(chunk_file_path, "r", encoding="utf-8") as f:
        content = f.read().split("\n--- 分割线 ---\n")
        for chunk in content:
            chunk = chunk.strip()
            if chunk and len(chunk) >= 10:  # 过滤空内容和过短片段
                chunks.append(chunk)
    
    print(f"成功加载 {len(chunks)} 个有效金融研报Chunk")
    return chunks

def get_embedding(text, openai_client):
    """
    调用硅基流动BGE-M3模型获取文本向量
    """
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"获取向量失败（文本片段前20字：{text[:20]}）：{e}")
        return None

def get_content_hash(text):
    """根据文本内容生成唯一的MD5哈希值"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def batch_insert_into_chroma(chunks, openai_client, collection):
    # 获取数据库里所有已存在的哈希ID
    existing_data = collection.get()
    existing_ids = set(existing_data["ids"])
    
    new_chunks = []
    new_embeddings = []
    new_ids = []
    
    for chunk in tqdm(chunks, desc="分析新内容"):
        # 【核心修改】使用内容哈希作为ID
        chunk_id = get_content_hash(chunk)
        
        # 如果这个内容的哈希值已在数据库中，说明是重复数据，直接跳过
        if chunk_id in existing_ids:
            continue
        
        # 获取向量
        embedding = get_embedding(chunk, openai_client)
        if not embedding:
            continue
        
        new_chunks.append(chunk)
        new_embeddings.append(embedding)
        new_ids.append(chunk_id)
    
    if new_chunks:
        collection.add(
            ids=new_ids,
            embeddings=new_embeddings,
            documents=new_chunks
        )
        print(f"✅ 成功增量更新 {len(new_chunks)} 个新片段")
    else:
        print("ℹ️ 未检测到新内容，数据库已是最新状态")

if __name__ == "__main__":
    try:
        # 1. 初始化客户端
        openai_client, collection = init_clients()
        
        # 2. 加载Chunk
        chunks = load_chunks_from_file(CHUNK_FILE_PATH)
        
        # 3. 批量入库
        batch_insert_into_chroma(chunks, openai_client, collection)
        
        # 4. 打印向量库统计信息
        collection_stats = collection.count()
        print(f"\n向量库 {COLLECTION_NAME} 总数据量：{collection_stats} 条")
    
    except Exception as e:
        print(f"程序运行失败：{e}")