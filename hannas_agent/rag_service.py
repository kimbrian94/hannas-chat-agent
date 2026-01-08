import os
import logging
from typing import List
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(
            self,
            document_path: str = None,
            vector_store_path: str = None,
            model_name: str = "gpt-4o-mini"):
        
        base_dir = Path(__file__).parent
        self.document_path = Path(document_path) if document_path else base_dir / "documents"
        self.vector_store_path = Path(vector_store_path) if vector_store_path else base_dir / "vector_store"
        self.model_name = model_name

        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.rag_chain = None
        self._session_store = {}

        logger.info(f"RAGService initialized with document_path: {self.document_path}")

    def setup(self):
        """One-time setup to initialize vector store and RAG chain"""
        self.load_and_index_documents()
        self.initialize_rag_chain()

    def load_and_index_documents(self):
        """Load documents from the documents directory"""
        logger.info(f"Loading documents from {self.document_path}")

        documents = []

        loaders = [
            (DirectoryLoader(str(self.document_path), glob="**/*.pdf", loader_cls=PyPDFLoader), "PDF"),
            (DirectoryLoader(str(self.document_path), glob="**/*.txt", loader_cls=TextLoader), "TXT"),
            (DirectoryLoader(str(self.document_path), glob="**/*.md", loader_cls=TextLoader), "MD")
        ]

        for loader, doc_type in loaders:
            try:
                loaded_docs = loader.load()
                documents.extend(loaded_docs)
                logger.info(f"Loaded {len(loaded_docs)} {doc_type} documents.")
            except Exception as e:
                logger.error(f"Error loading {doc_type} documents: {e}")
        if not documents:
            raise ValueError(f"No documents found in {self.document_path}")
                
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        logger.info(f"Loaded and split {len(documents)} documents into {len(splits)} chunks.")

        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=str(self.vector_store_path)
        )
        logger.info(f"Vector store created at {self.vector_store_path}")

    def initialize_rag_chain(self):
        """Initialize the conversational RAG chain"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized.")

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Hanna's Mom's Care Assistant. 
            Use the following context to answer questions about our postpartum care services.
            
            {context}
            
            If you don't know the answer, say so honestly."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o")

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        base_chain = (
            RunnablePassthrough.assign(
                context=lambda x: format_docs(retriever.invoke(x["input"]))
            )
            | prompt
            | llm
            | StrOutputParser()
        )
        
        self.rag_chain = RunnableWithMessageHistory(
            base_chain,
            get_session_history=self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        logger.info("RAG chain initialized.")

    def clear_session(self, session_id: str):
        """Clear chat history for a specific session ID"""
        if session_id in self._session_store:
            del self._session_store[session_id]
            logger.info(f"Cleared session history for session_id: {session_id}")
    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self._session_store:
            self._session_store[session_id] = InMemoryChatMessageHistory()
        return self._session_store[session_id]

    def ask(self, question: str, session_id: str) -> str:
        """Get response from RAG chain for a given question and session ID"""
        if not self.rag_chain:
            self.initialize_rag_chain()

        try:
            response = self.rag_chain.invoke(
                {"input": question},
                config={"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            logger.error(f"Error getting response from RAG chain: {e}")
            return "Sorry, I encountered an error."