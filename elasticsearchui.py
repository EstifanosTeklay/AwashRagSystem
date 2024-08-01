import streamlit as st
from elasticsearch import Elasticsearch
from groq import Groq
import json
import glob

# Initialize Groq client
client = Groq(api_key="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")

# Connect to Elasticsearch
es = Elasticsearch(
    hosts=[{
        'host': 'localhost',
        'port': 9200,
        'scheme': 'http'
    }]
)

# Index name
index_name = 'nbe_directives'

def search(query):
    # Search the Elasticsearch index
    results = es.search(
        index=index_name,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "source_file"]
                }
            }
        }
    )

    # Extract the relevant information from the search results
    hits = results['hits']['hits']
    search_results = []
    for hit in hits:
        search_results.append(hit['_source'])

    return search_results

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
