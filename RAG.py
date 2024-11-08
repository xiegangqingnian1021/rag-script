class RAG_Bot:

    def __init__(self, vector_db, llm_api, n_results=2):
        self.vector_db = vector_db
        self.llm_api = llm_api
        self.n_results = n_results
        self.prompt_template = """
你是一个问答机器人。
你的任务是根据下述给定的已知信息回答用户问题。
确保你的回复完全依据下述已知信息。不要编造答案。
如果下述已知信息不足以回答用户的问题，请直接回复"我无法回答您的问题"。

已知信息:
__INFO__

用户问：
__QUERY__

请用中文回答用户问题。
"""


    def chat_(self, user_query):
        # 1. 检索
        search_results = self.vector_db.search(user_query, self.n_results)

        # 2. 构建 Prompt
        # 从文档中查找到相关内容，构建提示词
        self.info = search_results['documents'][0]
        prompt = f"""已知信息: 
        {self.info}
        用户问：
        {user_query}
        """

        # 3. 调用 LLM
        response = self.llm_api(prompt)

        return response
