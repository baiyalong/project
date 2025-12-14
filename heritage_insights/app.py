import streamlit as st
import os
from services import EmbeddingService, VectorStore
from llm import OllamaLLM
from pipeline import RAGPipeline
from db_index import index_from_db
from config import settings

st.set_page_config(page_title="Heritage Insights", page_icon="🏛️", layout="wide")

st.title("🏛️ Heritage Insights - World Heritage Knowledge Base")

# Sidebar
with st.sidebar:
    st.header("System Control")
    
    # Model config
    model_name = st.text_input("Ollama Model Name", value=settings.OLLAMA_MODEL)
    ollama_url = st.text_input("Ollama URL", value=settings.OLLAMA_BASE_URL)
    
    st.divider()
    
    # ETL Control
    if st.button("🔄 Rebuild Index (ETL)"):
        with st.status("Indexing in progress...", expanded=True) as status:
            try:
                st.write("Initializing database connection...")
                db_url = settings.DATABASE_URL
                
                st.write("Reading data from Postgres and writing to vector store...")
                # Note: This is a synchronous call, might take time
                index_from_db(database_url=db_url)
                status.update(label="Index build completed!", state="complete", expanded=False)
                st.success("Data synchronization complete")
            except Exception as e:
                status.update(label="Index build failed", state="error")
                st.error(f"Error: {e}")

    st.divider()
    st.markdown("""
    ### About
    Use this tool to ask questions about World Heritage Sites.
    
    **Features:**
    - RAG (Retrieval-Augmented Generation)
    - Vector Search via ChromaDB
    - LLM via Ollama
    """)

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
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL) 
    vector_store = VectorStore(collection_name=settings.COLLECTION_NAME)
    llm = OllamaLLM(model=model_name, base_url=ollama_url)
    return RAGPipeline(embedding_service, vector_store, llm)

# User Input
if prompt := st.chat_input("Ask a question about World Heritage sites... (e.g., Where is the Great Wall?)"):
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
            
            if not docs:
                full_response = "I couldn't find any relevant documents in the knowledge base. Please try a different query or rebuild the index."
                response_placeholder.markdown(full_response)
            else:
                final_prompt = pipeline._build_prompt(prompt, docs)
                
                # Call Streaming LLM
                for chunk in pipeline.llm.stream_generate(final_prompt):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                
                # Show sources in an expander
                with st.expander("📚 View Retrieved Sources", expanded=False):
                    for idx, d in enumerate(docs):
                        st.markdown(f"**{idx+1}. {d.get('metadata', {}).get('source', d['id'])}**")
                        st.caption(f"Relevance Distance: {raw_results['distances'][0][idx] if 'distances' in raw_results else 'N/A'}")
                        st.text(d['text'][:500] + "...")
                        
        except Exception as e:
            full_response = f"⚠️ An error occurred: {str(e)}"
            response_placeholder.error(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
