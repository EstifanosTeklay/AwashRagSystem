import streamlit as st
import minsearch
import json
import glob
from groq import Groq
import time

# Initialize Groq client
client = Groq(api_key="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")

# Initialize an empty list to hold the flattened documents
documents = []

# Specify the correct path to the directory containing the JSON files
json_files_path = 'C:/Users/EstifanosT/AwashRagSystem/ConvertedToJson/*.json'

# Get the list of JSON files in the directory
json_files = glob.glob(json_files_path)

# Iterate over each JSON file in the directory
for json_file in json_files:
    try:
        with open(json_file, 'rt', encoding='utf-8') as f_in:
            doc_raw = json.load(f_in)
            # Check if 'pages' key exists in the JSON
            if 'pages' not in doc_raw:
                continue
            # Iterate over each page dictionary in the 'pages' list
            for page_dict in doc_raw['pages']:
                content = page_dict.get('content', '').strip()
                if content:  # Ensure the content is not empty
                    # Create a new dictionary to store the content and page number
                    doc = {
                        'page_number': page_dict.get('page_number', 'Unknown'),
                        'content': content,
                        'source_file': json_file  # Add the source file to track the origin
                    }
                    # Append the dictionary to the 'documents' list
                    documents.append(doc)
    except Exception as e:
        st.write(f"Error processing file {json_file}: {e}")

if not documents:
    st.error("No valid documents found for indexing. Ensure the documents have content.")
    st.stop()

# Create and fit the index with the combined documents
index = minsearch.Index(
    text_fields=["content"],
    keyword_fields=["page_number", "source_file"]
)

index.fit(documents)

def search(query):
    results = index.search(
        query=query,
        num_results=5
    )
    return results

def build_prompt(query, search_results):
    prompt_template = """
    You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the NBE directive.
    Use only the facts from the CONTEXT when answering the QUESTION.

    QUESTION: {question}

    CONTEXT:
    {context}
    """.strip()

    context = ""
    for doc in search_results:
        context += f"source_file: {doc['source_file']}\npage_number: {doc['page_number']}\ncontent: {doc['content']}\n\n"

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

def llm(prompt):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama3-8b-8192",
    )
    return response.choices[0].message.content

def rag(query):
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt)
    return answer

# Streamlit application
st.title("Awash Bank RAG System")
query = st.text_input("Enter your question:")

if st.button("Ask"):
    with st.spinner("Processing..."):
        answer = rag(query)
    st.write("Answer:")
    st.write(answer)

