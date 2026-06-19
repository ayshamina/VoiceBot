from langchain_community.embeddings import HuggingFaceEmbeddings
print("Loading embeddings model...")
try:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    print("Embedding query...")
    res = embeddings.embed_query("test query")
    print("Success! Embedding length:", len(res))
except Exception as e:
    print("Failed with error:", e)
