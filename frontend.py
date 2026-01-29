import streamlit as st
from rag_chain import rag_qa_pipeline
from data_process import extract_clean_text_from_pdf, split_text_into_chunks
from build_vector_db import batch_insert_into_chroma, init_clients

# ===================== 核心修改：适配你的项目路径（无额外新增，复用其他文件的配置） =====================
# 页面配置
st.set_page_config(page_title="金融研报问答助手", page_icon="📈")
st.title("📈研报问答助手")

# 初始化会话状态（保存聊天记录）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏：上传PDF（可选，补充向量库）
with st.sidebar:
    st.header("📤 补充研报")
    uploaded_file = st.file_uploader("上传PDF研报", type="pdf")
    if uploaded_file is not None:
        with st.spinner("处理PDF并入库..."):
            # 提取清洗文本
            clean_text = extract_clean_text_from_pdf(uploaded_file)
            # 切分Chunk
            chunks = split_text_into_chunks(clean_text)
            # 初始化客户端并入库
            openai_client, collection = init_clients()
            batch_insert_into_chroma(chunks, openai_client, collection)
            st.success(f"上传成功！新增 {len(chunks)} 个研报片段")

# 显示历史聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 接收用户提问
if prompt := st.chat_input("请输入你的问题（如：人工智能行业的发展前景如何？）"):
    # 记录用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用RAG流程生成回答
    with st.chat_message("assistant"):
        with st.spinner("正在检索研报并生成回答..."):
            response = rag_qa_pipeline(prompt)
            st.markdown(response)
    # 记录助手消息
    st.session_state.messages.append({"role": "assistant", "content": response})