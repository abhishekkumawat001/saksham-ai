from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_faqs(lang: str = 'hi'):
    return []

@router.get("/search")
def search_faqs(q: str):
    # Semantic search with text-embedding-3-small + pgvector / pinecone
    return []
