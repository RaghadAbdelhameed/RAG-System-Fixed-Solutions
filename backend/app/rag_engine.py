"""
The actual RAG pipeline:
1. retrieve_chunks() -> pgvector cosine-similarity search, scoped to one org
2. generate_answer() -> sends retrieved context + question to Gemini
3. answer_question() -> glues the two together with a fallback for low relevance
"""
from functools import lru_cache

import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text

from .config import settings
from .ingestion import embed_query

FALLBACK_MESSAGE = (
    "لا تتوفر لدي معلومات كافية للإجابة على هذا السؤال ضمن مستندات مؤسستكم الحالية. "
    "برجاء إعادة صياغة السؤال أو التواصل مع الفريق المختص."
)

SYSTEM_INSTRUCTIONS = """أنت مساعد معرفي داخلي لمؤسسة واحدة فقط. أجب حصراً بالاعتماد على
المقاطع المرفقة أدناه، بأي لغة كتب بها السؤال (عربي أو إنجليزي)، حتى لو كانت المقاطع نفسها
بلغة مختلفة عن لغة السؤال - في هذه الحالة ترجم المعنى ولا تذكر نص المقطع الأصلي حرفياً.
لا تخترع أي معلومة غير موجودة في المقاطع. اذكر أرقام المصادر [1] [2] المستخدمة بجانب كل جملة.
إذا كانت المقاطع لا تحتوي على إجابة كافية، قل ذلك بوضوح بدلاً من التخمين."""


@lru_cache(maxsize=1)
def get_gemini_model():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_INSTRUCTIONS,
    )


def retrieve_chunks(db: Session, organization_id, question: str, top_k: int = None):
    top_k = top_k or settings.TOP_K
    query_vec = embed_query(question)

    # pgvector cosine distance operator: <=>  (0 = identical, 2 = opposite)
    rows = db.execute(
        sql_text(
            """
            SELECT kc.content, kf.filename, 1 - (kc.embedding <=> :qvec) AS similarity
            FROM knowledge_chunks kc
            JOIN knowledge_files kf ON kf.id = kc.file_id
            WHERE kc.organization_id = :org_id
            ORDER BY kc.embedding <=> :qvec
            LIMIT :k
            """
        ),
        {"qvec": str(query_vec), "org_id": str(organization_id), "k": top_k},
    ).fetchall()

    return [{"content": r.content, "source": r.filename, "similarity": float(r.similarity)} for r in rows]


def generate_answer(question: str, chunks: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[{i+1}] (المصدر: {c['source']})\n{c['content']}" for i, c in enumerate(chunks)
    )
    prompt = f"""المقاطع المسترجعة:

{context_block}

سؤال المستخدم: {question}"""

    model = get_gemini_model()
    response = model.generate_content(prompt)
    return (response.text or "").strip()


def answer_question(db: Session, organization_id, question: str):
    chunks = retrieve_chunks(db, organization_id, question)

    if not chunks or chunks[0]["similarity"] < settings.RELEVANCE_THRESHOLD:
        return {
            "answer": FALLBACK_MESSAGE,
            "was_fallback": True,
            "sources": [],
        }

    # keep only reasonably relevant chunks for the prompt
    relevant = [c for c in chunks if c["similarity"] >= settings.RELEVANCE_THRESHOLD] or chunks[:1]
    answer_text = generate_answer(question, relevant)
    sources = sorted(set(c["source"] for c in relevant))

    return {"answer": answer_text, "was_fallback": False, "sources": sources}
