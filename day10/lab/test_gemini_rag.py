import os
import sys

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from google import genai
except ImportError:
    print("Vui lòng cài đặt: pip install chromadb sentence-transformers google-genai")
    sys.exit(1)

from dotenv import load_dotenv

def main():
    load_dotenv()
    
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env")
        return 1

    client_genai = genai.Client(api_key=gemini_api_key)
    model_name = 'gemini-2.5-flash'

    # Khởi tạo ChromaDB
    db_path = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    collection_name = os.environ.get("CHROMA_COLLECTION", "day10_kb")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=db_path)
    emb = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    col = client.get_collection(name=collection_name, embedding_function=emb)

    print("🤖 Chatbot RAG đã sẵn sàng! (Gõ 'quit' để thoát)")

    while True:
        try:
            question = input("\n💬 Nhập câu hỏi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nTạm biệt!")
            break
            
        if question.lower() == 'quit':
            print("Tạm biệt!")
            break
        if not question:
            continue

        # Truy xuất context
        res = col.query(query_texts=[question], n_results=5)
        docs = res.get("documents", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        
        context_text = ""
        print("\n🔍 TÀI LIỆU TRÍCH XUẤT ĐƯỢC (TOP RETRIEVAL):")
        for i, (doc, meta) in enumerate(zip(docs, metadatas), 1):
            doc_id = meta.get("doc_id", "Unknown")
            print(f"  [Top {i}] doc_id: {doc_id}")
            context_text += f"\n--- [Nguồn: {doc_id}] ---\n{doc}"
        
        # Prompt cho LLM
        prompt = f"""
Bạn là trợ lý ảo hỗ trợ CS và IT (Helpdesk) của công ty.
Dựa vào ngữ cảnh (Context) được cung cấp dưới đây, hãy trả lời câu hỏi của người dùng.
Chỉ trả lời dựa trên thông tin trong ngữ cảnh. Trả lời ngắn gọn, chính xác.

=== CONTEXT ===
{context_text}
===============

CÂU HỎI: {question}
TRẢ LỜI:"""

        print("\nĐang gọi Gemini API...")
        try:
            response = client_genai.models.generate_content(model=model_name, contents=prompt)
            print("="*50)
            print("💡 CÂU TRẢ LỜI TỪ GEMINI:")
            print("="*50)
            print(response.text.strip())
            print("="*50)
        except Exception as e:
            print(f"❌ Lỗi khi gọi Gemini: {e}")

if __name__ == "__main__":
    sys.exit(main())
