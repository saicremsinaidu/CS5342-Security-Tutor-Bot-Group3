Docker Setup - qdrant Vector Database Setup

-> Install Docker and enable terminal
-> Run Below commands to start the qdrant Vector Database
	1. docker pull qdrant/qdrant # download qdrant into docker
	2. docker run -p 6333:6333 qdrant/qdrant # qdrant instance will be started on port 6333


Install packages:

a. sentencetransformers : Embedding model of the project
b. qdrant_client : Connections to the qdrant database
c. gradio : Front-end web page
d. gpt4all : LLM model of the project 
e. fitz : conversion of pdf files to text files to support use in sentence transformers



Operation:

1. Run initialise_qdrant.py to create a new collection in the qdrant DB
2. Place all the knowledge documents in one path and modify the pdf_path in the Data_insertion_qdrant.py
3. Run Data_insertion_qdrant.py which will load each page into the qdrant DB which will help in actively pointing referencing the document and page number.
4. Run Chatbot_application.py to start the local host and connection to qdrant DB, the local host is used to input query and receive the response from the vector DB if present or else connect to internet via a API to collect the data required.


# In One Tab
# docker pull qdrant/qdrant
# docker run -p 6333:6333 qdrant/qdrant

# In Second Tab
# python -m venv venv 

# for Mac Only , For windows skip this one
# source venv/bin/activate 

# for Windows only , For Mac skip this one
# venv\Scripts\activate

# If you get a permission error in windows (skip this for MAC)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser


# pip install fuzzywuzzy python-Levenshtein sentence-transformers qdrant-client gradio gpt4all pymupdf
# python Scripts/initialise_qdrant.py 
# python Scripts/Data_insertion_qdrant.py                           
# python Scripts/chatbot_application.py 