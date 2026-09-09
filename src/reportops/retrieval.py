from pathlib import Path

from google import genai
from google.genai import types
import chromadb
from dotenv import load_dotenv
from functools import lru_cache
from pypdf import PdfReader
import re

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

def load_pdf_sections(path: str | Path) -> list[dict]:
    """Load a pdf and split it into sections"""

    path = Path(path)
    reader = PdfReader(path)

    sections = []
    current_heading = reader.pages[0].extract_text().split('\n')[0]
    current_lines = []
    start_page = 1

    for page_no, page in enumerate(reader.pages, start=1):
        
        text = page.extract_text()

        for line in text.splitlines():
            if re.match(r"^\d+\.", line.strip()):
                sections.append({
                    "section": current_heading,
                    "text": "\n".join(current_lines).strip(),
                    "page": start_page
                })

                current_heading = line
                current_lines = [line]
                start_page = page_no
            else:
                current_lines.append(line)

    sections.append({
        "section": current_heading,
        "text": "\n".join(current_lines).strip(),
         "page": start_page
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

def load_pdf_fixed_chunks(
    path: str | Path,
    chunk_size: int = 500,
) -> list[dict]:
    """Load the pdf and split it into fixed-size character chunks."""

    path = Path(path)
    reader = PdfReader(path)

    chunks = []

    for page_no, page in enumerate(reader.pages, start=1):
            
        text = page.extract_text()

        for start in range(0, len(text), chunk_size):
            chunk_text = text[start:start + chunk_size]

            chunks.append({
                "section": f"chunk_{len(chunks)}",
                "text": chunk_text.strip(),
                "page": page_no
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

def build_reporting_collection(
    handbook_sections: list[dict],
    pdf_sections: list[dict],
    collection_name: str = "reporting_knowledge",
):
    """Create a Chroma collection containing the reporting sections."""

    client = chromadb.Client()

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=None,
    )

    for section in handbook_sections:
        section["document"] = "ReportOps Reporting Handbook"
        section["source_type"] = "markdown"
    for section in pdf_sections:
        section["document"] = "ReportOps Reporting Escalation Policy"
        section["source_type"] = "pdf"
    all_sections = handbook_sections + pdf_sections

    texts = [section["text"] for section in all_sections]

    embeddings = create_embeddings(
        texts=texts,
        task_type="RETRIEVAL_DOCUMENT",
    )

    ids = [f"section_{i}" for i in range(len(texts))]

    metadatas = [
        {
            "document": section["document"],
            "source_type":section["source_type"],
            "section": section["section"],
            **( {"page": section["page"]} if section["source_type"]=="pdf" else {} )
        }
        for section in all_sections
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return collection

@lru_cache(maxsize=1)
def get_reporting_collection():
    """Load the reporting knowledge and return its Chroma collection."""

    handbook_path = Path("docs/reporting_handbook/reporting_handbook.md")
    pdf_path = Path("docs/reporting_handbook/reporting_escalation_policy.pdf")

    handbook_sections = load_handbook_sections(handbook_path)
    pdf_sections = load_pdf_sections(pdf_path)

    collection = build_reporting_collection(handbook_sections, pdf_sections)

    return collection

def retrieve_reporting_rules(
    question: str,
    collection,
    n_results: int = 3,
) -> list[dict]:
    """Retrieve the sections most relevant to a user question."""

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
            "document": metadata["document"],
            "source_type": metadata["source_type"],
            "section": metadata["section"],
            "text": document,
            "distance": distance,
            **( {"page": metadata["page"]} if metadata["source_type"]=="pdf" else {} )
        })

    return retrieved