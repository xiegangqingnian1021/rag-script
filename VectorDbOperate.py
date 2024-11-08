import chromadb


class MyVectorDBConnector:
    def __init__(self, collection_name, embedding_fn, host_ip="192.168.105.100", host_port="8000"):
        # 创建Client客户端
        # chroma_client = chromadb.Client()
        chroma_client = chromadb.HttpClient(host=host_ip, port=host_port)

        # 创建一个 collection，collection_name 为 对话编号
        self.collection = chroma_client.get_or_create_collection(name=collection_name)
        self.embedding_fn = embedding_fn


    def add_documents(self, documents):
        """向 collection 中添加文档与向量"""
        self.collection.add(
            embeddings=self.embedding_fn(documents),  # 每个文档的向量
            documents=documents,  # 文档的原文
            ids=[f"id{i}" for i in range(len(documents))]  # 每个文档的 id
        )

    def search(self, query, top_n):
        """检索向量数据库"""
        results = self.collection.query(
            query_embeddings=self.embedding_fn([query]),
            n_results=top_n
        )
        return results