import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

class LogRetriever:
    """
    Handles the ingestion, indexing, and retrieval of unstructured log data.
    Uses LlamaIndex with Google Gemini embeddings.
    """

    def __init__(self, log_dir="data/logs"):
        print(f"🔄 Initializing LogRetriever for directory: {log_dir}...")

        # Load API Key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        # 1. Configure Settings to use Gemini
        # We use Gemini for both embedding (vectorizing text) and LLM tasks within LlamaIndex
        print(f"⚙️ Configuring LlamaIndex to use Google Gemini...")
        try:
            Settings.llm = Gemini(model="gemini-3-flash-preview", api_key=api_key)
            Settings.embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key)
        except Exception as e:
            print(f"⚠️ Warning: LlamaIndex settings failed. {e}")

        # 2. Load Data (Ingestion)
        # SimpleDirectoryReader automatically reads all files in the directory
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"⚠️ Warning: Log directory '{log_dir}' created but is empty.")

        reader = SimpleDirectoryReader(input_dir=log_dir)
        documents = reader.load_data()
        print(f"📄 Loaded {len(documents)} log documents.")

        # 3. Create Vector Index
        # This creates an in-memory vector store. For production, use ChromaDB or Pinecone.
        self.index = VectorStoreIndex.from_documents(documents)

        # 4. Create Retriever Engine
        # similarity_top_k=5 means we fetch the top 5 most relevant log chunks
        self.retriever_engine = self.index.as_retriever(similarity_top_k=5)
        print("✅ LogRetriever is ready.")

    def get_relevant_logs(self, query_text: str) -> str:
        """
        Retrieves relevant log snippets based on the user's query.
        Returns a formatted string containing the log context.
        """
        try:
            nodes = self.retriever_engine.retrieve(query_text)

            context_str = "\n--- RELEVANT LOG ENTRIES (Retrieval) ---\n"
            for node in nodes:
                # node.score indicates similarity confidence (optional to filter)
                context_str += f"[Score: {node.score:.2f}] Content: {node.text}\n"
            context_str += "----------------------------------------\n"

            return context_str
        except Exception as e:
            return f"Error retrieving logs: {str(e)}"

# For testing independently
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    retriever = LogRetriever()
    result = retriever.get_relevant_logs("What happened to the BMS firmware v2.1.0?")
    print(result)