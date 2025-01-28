import os
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"  # Replace with your OpenAI API key
from langchain.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import nltk

# Load NLTK resources if not already downloaded
nltk.download('punkt_tab', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)

# Load documents from URL
loader = UnstructuredURLLoader(urls=["https://brainlox.com/courses/category/technical"])
data = loader.load()

# Print the loaded data and the number of documents
print("Loaded data: {}".format(str(data)))
print("Number of documents loaded: {}".format(len(data)))

# Check if data is empty and handle the case
if not data:
    print("No data loaded. Check the URL or website accessibility.")
    raise ValueError("No data loaded from the specified URL.")

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = text_splitter.split_documents(data)

# Print the number of documents after splitting
print("Number of documents after splitting: {}".format(len(documents)))

# Generate embeddings and store in Chroma
embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
persist_directory = 'db'
vectordb = Chroma.from_documents(documents, embeddings, persist_directory=persist_directory)
vectordb.persist()
print("Embeddings generated and stored in Chroma vector store.")

# Initialize LLM and QA chain
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
app = Flask(__name__)
api = Api(app)

class Chatbot(Resource):
    def post(self):
        query = request.get_json()['query']
        result = qa({"query": query})
        return jsonify({"response": result['result']})

class Conversation(Resource):
    def post(self):
        data = request.get_json()
        user_message = data.get('message')
        return jsonify({"response": "You said: {}".format(user_message)})

api.add_resource(Chatbot, '/chatbot')
api.add_resource(Conversation, '/conversation')

if __name__ == '__main__':
    app.run(debug=True)
