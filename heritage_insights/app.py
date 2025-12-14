import streamlit as st
import os
from services import EmbeddingService, VectorStore
from llm import OllamaLLM
from pipeline import RAGPipeline
from db_index import index_from_db

st.set_page_config(page_title="Heritage Insights", page_icon="🏛️", layout="wide")

st.title("🏛️ Heritage Insights - 私有世界遗产知识库")

# Sidebar
with st.sidebar:
    st.header("系统控制")
    
    # Model config
    model_name = st.text_input("Ollama 模型名称", value="llama3.2")
    ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    
    st.divider()
    
    # ETL Control
    if st.button("🔄 重建索引 (ETL)"):
        with st.status("正在建立索引...", expanded=True) as status:
            try:
                st.write("初始化数据库连接...")
                db_url = os.getenv("DATABASE_URL")
                if not db_url:
                    # Fallback default for local dev
                    db_url = "postgresql://heritage_user:heritage_password@localhost:5432/heritage"
                
                st.write("开始从 Postgres 读取数据并写入向量库...")
                # Note: This is a synchronous call, might take time
                index_from_db(database_url=db_url)
                status.update(label="索引构建完成!", state="complete", expanded=False)
                st.success("数据已同步完成")
            except Exception as e:
                status.update(label="索引构建失败", state="error")
                st.error(f"Error: {e}")

# Main Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialization (Lazy load)
@st.cache_resource
def get_pipeline(model_name, ollama_url):
    embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2") # Or BAAI/bge-m3 if desired, but using default from services.py
    vector_store = VectorStore()
    llm = OllamaLLM(model=model_name, base_url=ollama_url)
    return RAGPipeline(embedding_service, vector_store, llm)

# User Input
if prompt := st.chat_input("请输入关于世界遗产的问题... (例如: 长城在哪里?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            pipeline = get_pipeline(model_name, ollama_url)
            
            # Step 1: Retrieval (We can do this explicitly if we want to show docs, or just call answer)
            # For streaming, we need to adapt RAGPipeline a bit or just use llm.stream_generate with the prompt built by pipeline
            
            # Replicating pipeline logic to support streaming:
            q_emb = pipeline.embedding_service.embed_query(prompt)
            raw_results = pipeline.vector_store.query(q_emb, n_results=3)
            
            # Parse results
            docs = []
            ids = raw_results.get('ids', [[]])[0]
            documents = raw_results.get('documents', [[]])[0]
            metadatas = raw_results.get('metadatas', [[]])[0]
            
            for i in range(len(ids or [])):
                docs.append({
                    'id': ids[i],
                    'text': documents[i] if documents else '',
                    'metadata': metadatas[i] if metadatas else {},
                })
            
            final_prompt = pipeline._build_prompt(prompt, docs)
            
            # Call Streaming LLM
            for chunk in pipeline.llm.stream_generate(final_prompt):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # Optional: Show sources in an expander
            if docs:
                with st.expander("参考来源 (Sources)"):
                    for d in docs:
                        st.markdown(f"**ID: {d['id']}**")
                        st.text(d['text'][:200] + "...")
                        
        except Exception as e:
            full_response = f"⚠️ Error: {str(e)}"
            response_placeholder.error(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
