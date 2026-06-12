"""Knowledge base / RAG package for KisanSaathi.

Pipeline: synthetic corpus (+ optional scraped pages) -> chunk -> embed with a
HuggingFace MiniLM model -> store in ChromaDB -> retrieve -> answer with Groq.
"""
