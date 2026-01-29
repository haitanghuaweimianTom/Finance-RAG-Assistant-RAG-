import os
from tqdm import tqdm
import pdfplumber

# ===================== 核心修改：适配你的项目路径 =====================
# 配置路径（完全匹配你的项目文件夹结构，注意PDF文件夹名是 data-rawpdf）
RAW_PDF_DIR = "./data-rawpdf"  # 你的原始PDF文件夹（相对路径，直接对应项目根目录下的 data-rawpdf）
CLEAN_TEXT_DIR = "./clean_texts"  # 生成的纯净文本存放目录（项目根目录下）
CHUNK_OUTPUT_DIR = "./chunks"  # 生成的Chunk存放目录（项目根目录下）

# 配置Chunk参数（500字每段，50字重叠）
CHUNK_SIZE = 500  # 每个片段的字数
OVERLAP_SIZE = 50  # 相邻片段的重叠字数

def create_dirs():
    """创建必要的文件夹"""
    for dir_path in [CLEAN_TEXT_DIR, CHUNK_OUTPUT_DIR, RAW_PDF_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

def extract_clean_text_from_pdf(pdf_path):
    """
    从PDF中提取纯净正文（去除页眉、页脚、乱码、多余空白）
    """
    clean_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # 提取页面文本
                page_text = page.extract_text()
                if not page_text:
                    continue
                
                # 清洗文本（针对金融研报的针对性处理）
                lines = page_text.split("\n")
                for line in lines:
                    line = line.strip()
                    # 过滤无效内容（页眉页脚常见特征：页码、日期、券商名称缩写等）
                    if not line:
                        continue
                    if any(keyword in line for keyword in ["第 ", "页", "2024", "2025", "券商名称", "研究所"]):
                        # 可根据你的PDF页眉页脚特征补充关键词
                        continue
                    # 过滤过短的无意义行（如单个数字、符号）
                    if len(line) < 5:
                        continue
                    
                    clean_text += line + " "
            
            # 去除多余空白，使文本更紧凑
            clean_text = " ".join(clean_text.split())
    
    except Exception as e:
        print(f"处理PDF {pdf_path} 失败：{e}")
    
    return clean_text

def split_text_into_chunks(text):
    """
    将纯净文本按「500字Chunk+50字重叠」切分
    """
    chunks = []
    text_length = len(text)
    
    # 如果文本长度小于Chunk大小，直接作为一个片段
    if text_length <= CHUNK_SIZE:
        chunks.append(text)
        return chunks
    
    # 滑动窗口切分（实现重叠效果）
    start = 0
    while start < text_length:
        # 计算当前片段的结束位置
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append(chunk)
        
        # 下一个片段的起始位置 = 当前起始位置 + Chunk大小 - 重叠大小
        start += (CHUNK_SIZE - OVERLAP_SIZE)
        
        # 防止最后一个片段过短（小于重叠大小），合并到上一个片段
        if (text_length - start) < OVERLAP_SIZE:
            break
    
    return chunks

def process_all_pdfs():
    """
    批量处理所有PDF文件，完成清洗和Chunk切分
    """
    create_dirs()
    
    # 获取所有PDF文件
    pdf_files = [f for f in os.listdir(RAW_PDF_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"未在 {RAW_PDF_DIR} 文件夹中找到任何PDF文件！")
        return
    
    # 批量处理
    all_chunks = []
    for pdf_file in tqdm(pdf_files, desc="处理PDF文件"):
        pdf_path = os.path.join(RAW_PDF_DIR, pdf_file)
        
        # 1. 提取纯净正文
        clean_text = extract_clean_text_from_pdf(pdf_path)
        if not clean_text:
            continue
        
        # 2. 保存纯净文本（可选，便于排查问题）
        text_filename = os.path.splitext(pdf_file)[0] + ".txt"
        text_path = os.path.join(CLEAN_TEXT_DIR, text_filename)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(clean_text)
        
        # 3. 切分Chunk
        chunks = split_text_into_chunks(clean_text)
        all_chunks.extend(chunks)
        
        # 4. 保存当前PDF的Chunk（可选）
        chunk_filename = os.path.splitext(pdf_file)[0] + "_chunks.txt"
        chunk_path = os.path.join(CHUNK_OUTPUT_DIR, chunk_filename)
        with open(chunk_path, "w", encoding="utf-8") as f:
            for idx, chunk in enumerate(chunks):
                f.write(f"=== Chunk {idx+1} ===\n")
                f.write(chunk)
                f.write("\n\n")
    
    # 5. 保存所有Chunk到总文件（方便后续向量化使用）
    total_chunk_path = os.path.join(CHUNK_OUTPUT_DIR, "all_finance_chunks.txt")
    with open(total_chunk_path, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(all_chunks):
            f.write(chunk)
            f.write("\n--- 分割线 ---\n")
    
    print(f"数据处理完成！")
    print(f"1. 纯净文本保存至：{CLEAN_TEXT_DIR}")
    print(f"2. 分片Chunk保存至：{CHUNK_OUTPUT_DIR}")
    print(f"3. 总Chunk数：{len(all_chunks)} 个")

if __name__ == "__main__":
    process_all_pdfs()