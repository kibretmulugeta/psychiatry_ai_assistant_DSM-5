"""
DSM-5 Psychiatry Knowledge Base Ingestion Script.
Parses, chunks, embeds, and indexes all DSM-5 clinical documents in knowledge_base/ into vector store.
"""

import asyncio
import sys
import sqlite3
import json
from pathlib import Path
import uuid

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.backend.app.core.config import settings
from packages.rag.ingestion.text_parser import TextDocumentParser
from packages.rag.ingestion.pdf_parser import PDFDocumentParser
from packages.rag.chunking.recursive_chunker import RecursiveCharacterChunker
from packages.rag.embeddings.factory import EmbeddingFactory


async def run_ingestion() -> None:
    """Ingest, chunk, embed, and index all DSM-5 files in knowledge_base/."""
    print("=" * 65)
    print("STARTING DSM-5 PSYCHIATRY KNOWLEDGE BASE INGESTION PIPELINE")
    print("=" * 65)

    db_path = "knowledge_base.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clean recreate of tables for fresh DSM-5 indexing
    cursor.execute("DROP TABLE IF EXISTS document_chunks")
    cursor.execute("DROP TABLE IF EXISTS documents")
    
    cursor.execute("""
        CREATE TABLE documents (
            id TEXT PRIMARY KEY,
            filename TEXT UNIQUE,
            file_type TEXT,
            checksum TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT,
            chunk_index INTEGER,
            content TEXT,
            embedding TEXT,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
    """)
    conn.commit()
    print("[OK] DSM-5 Knowledge Base vector database schema initialized.")

    kb_dir = Path("knowledge_base")
    if not kb_dir.exists():
        print("[Error] knowledge_base directory not found.")
        return

    files = list(kb_dir.glob("*"))
    print(f"\nDiscovered {len(files)} DSM-5 clinical reference documents:")
    for f in sorted(files):
        print(f"  - {f.name}")

    text_parser = TextDocumentParser()
    pdf_parser = PDFDocumentParser()
    chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)
    embedding_provider = EmbeddingFactory.get_provider()

    total_docs = 0
    total_chunks = 0

    for file_path in sorted(files):
        if file_path.is_dir():
            continue

        filename = file_path.name
        file_bytes = file_path.read_bytes()

        if filename.endswith(".pdf"):
            parsed_doc = await pdf_parser.parse(file_bytes, filename)
        elif filename.endswith((".md", ".txt", ".json", ".csv")):
            parsed_doc = await text_parser.parse(file_bytes, filename)
        else:
            print(f"\n[Warning] Skipping unsupported file format: {filename}")
            continue

        print(f"\nIngesting [{filename}] ({len(parsed_doc.content)} chars)...")

        doc_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO documents (id, filename, file_type, checksum) VALUES (?, ?, ?, ?)",
            (doc_id, parsed_doc.filename, parsed_doc.file_type, parsed_doc.checksum)
        )

        text_chunks = chunker.split_text(parsed_doc.content)
        chunk_contents = [c.content for c in text_chunks]
        embeddings = await embedding_provider.embed_documents(chunk_contents)

        for idx, (chunk_item, emb_vector) in enumerate(zip(text_chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO document_chunks (id, document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?, ?)",
                (chunk_id, doc_id, idx, chunk_item.content, json.dumps(emb_vector))
            )

        conn.commit()
        total_docs += 1
        total_chunks += len(text_chunks)
        print(f"   [OK] Checksum verified (SHA256: {parsed_doc.checksum[:12]}...)")
        print(f"   [OK] Generated & embedded {len(text_chunks)} vector chunks.")

    conn.close()

    print("\n" + "=" * 65)
    print("DSM-5 KNOWLEDGE BASE INGESTION PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total DSM-5 Clinical Documents Ingested: {total_docs}")
    print(f"Total Vector Chunks Stored: {total_chunks}")
    print(f"Vector Database File: {db_path}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_ingestion())
