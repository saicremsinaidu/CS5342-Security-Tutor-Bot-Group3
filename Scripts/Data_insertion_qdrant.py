import fitz   # PyMuPDF - used for reading PDF files page by page
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os
import uuid # Used to generate unique IDs for each stored page

# ------------------------------------------------------------
# Load the SentenceTransformer model
# This model converts text into a 384-dimensional embedding,
# which is used by Qdrant for semantic search.
# ------------------------------------------------------------
embedder = SentenceTransformer('all-MiniLM-L12-v2')  

# Connect to Qdrant (Ensure Qdrant is running on localhost:6333)
qdrant_client = QdrantClient(host="localhost", port=6333)
collection_name = "network_security_knowledge"

# Function to extract text from PDF and store it in Qdrant
def process_pdfs(directory):
    page_texts = []
    
    # List PDF files in the given directory
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)  # Get full path for the PDF
        doc = fitz.open(pdf_path)  # Open the PDF using its full path
        
        # Iterate over the pages and extract text
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            page_texts.append((pdf_file, page_num + 1, text))  # Store (doc_name, page_num, text)
        
    # Insert each page's text into Qdrant (indexed by document name and page number)
    for doc_name, page_num, text in page_texts:
        # Generate embedding for the text of the page
        embedding = embedder.encode([text])[0]  # Text embedding
        
        # Generate a unique UUID for each page
        point_id = str(uuid.uuid4())  # Generate a unique UUID
        
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[{
                "id": point_id,  # Use UUID as the point ID
                "vector": embedding.tolist(),
                "payload": {
                    "document": doc_name,
                    "page_number": page_num,
                    "text": text[:500]  # Store the first 500 characters for reference
                }
            }]
        )
    # Final summary after processing all PDFs
    print(f"Processed {len(page_texts)} pages from {len(pdf_files)} documents")

if __name__ == "__main__":
    # Provide the directory containing the PDFs
    pdf_path = r"/Users/naveensaicremsiyadlapalli/Downloads/NS_Project_GP1_Final(Updated)/knowledge_base"
    process_pdfs(pdf_path)
