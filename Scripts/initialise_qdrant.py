# scripts/init_qdrant.py

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams



"""
    Initialize (or recreate) a Qdrant collection used for storing
    vector embeddings of our Network Security knowledge base.

    This script should be run ONLY ONCE during setup to create
    a fresh collection before inserting any documents.
"""


def initialize_qdrant():
   
    # Connect to the local Qdrant instance running on Docker (port 6333)
    qdrant_client = QdrantClient(host="localhost", port=6333)

    # Define and create a collection with vector configuration
    qdrant_client.recreate_collection(
        collection_name="network_security_knowledge",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    # Connect to the local Qdrant instance running on Docker (port 6333)
    print("Qdrant collection 'network_security_knowledge' initialized successfully.")

# When running this file directly (python init_qdrant.py), initialize the collection.
if __name__ == "__main__":
    initialize_qdrant()
