from pathlib import Path

from google import genai
from google.genai import types
import chromadb
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

def load_handbook_sections(path: str | Path) -> list[dict]:
    """Load a Markdown handbook and split it into sections based on ## headings."""

    path = Path(path)
    text = path.read_text(encoding="utf-8")

    sections = []
    current_heading = None
    current_lines = []

    for line in text.splitlines():

        if line.startswith("## "):
            if current_heading is not None:
                sections.append({
                    "section": current_heading,
                    "text": "\n".join(current_lines).strip()
                })

            current_heading = line.removeprefix("## ").strip()
            current_lines=[line]
        else:
            current_lines.append(line)

    sections.append({
        "section": current_heading,
        "text": "\n".join(current_lines).strip()
    })

    return sections

def load_handbook_fixed_chunks(
    path: str | Path,
    chunk_size: int = 500,
) -> list[dict]:
    """Load the handbook and split it into fixed-size character chunks."""

    path = Path(path)
    text = path.read_text(encoding="utf-8")

    chunks = []

    for start in range(0, len(text), chunk_size):
        chunk_text = text[start:start + chunk_size]

        chunks.append({
            "section": f"chunk_{len(chunks)}",
            "text": chunk_text.strip()
        })

    return chunks

def create_embeddings(
    texts: list[str],
    task_type: str,
) -> list[list[float]]:
    """Create Gemini embeddings for a list of text strings."""

    client = genai.Client()

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
        ),
    )

    return [embedding.values for embedding in result.embeddings]

def build_handbook_collection(sections: list[dict]):
    """Create a Chroma collection containing the reporting handbook sections."""

    client = chromadb.Client()

    collection = client.get_or_create_collection(
        name="reporting_handbook",
        embedding_function=None,
    )

    texts = [section["text"] for section in sections]

    embeddings = create_embeddings(
        texts=texts,
        task_type="RETRIEVAL_DOCUMENT",
    )

    ids = [f"section_{i}" for i in range(len(texts))]

    metadatas = [
        {
            "document": "ReportOps Reporting Handbook",
            "section": section["section"],
        }
        for section in sections
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return collection

@lru_cache(maxsize=1)
def get_handbook_collection():
    """Load the reporting handbook and return its Chroma collection."""

    handbook_path = Path("docs/reporting_handbook/reporting_handbook.md")

    sections = load_handbook_sections(handbook_path)

    collection = build_handbook_collection(sections)

    return collection

def retrieve_reporting_rules(
    question: str,
    collection,
    n_results: int = 3,
) -> list[dict]:
    """Retrieve the handbook sections most relevant to a user question."""

    query_embedding = create_embeddings(
        texts=[question],
        task_type="RETRIEVAL_QUERY",
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    retrieved = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "section": metadata["section"],
            "document": metadata["document"],
            "text": document,
            "distance": distance
        })

    return retrieved