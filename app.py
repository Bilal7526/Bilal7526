from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# Configuration (replace with your actual values)
search_endpoint = "https://<your-search-service>.search.windows.net"
search_index = "incidents-index"
search_api_key = "<your-search-admin-key>"

openai_endpoint = "https://<your-openai-resource>.openai.azure.com"
openai_deployment = "<your-chat-model-deployment-name>"  # e.g., "gpt35"
openai_api_key = "<your-openai-key>"

# HTML template for form input
HTML_FORM = """
<!doctype html>
<title>Ask a Question</title>
<h2>Ask a Cybersecurity Question</h2>
/ask
  <input type="text" name="question" placeholder="Enter your question" size="60">
  <input type="submit" value="Ask">
</form>
{% if answer %}
  <h3>Answer:</h3>
  <p>{{ answer }}</p>
{% endif %}
"""

@app.route('/ask', methods=['GET'])
def ask():
    question = request.args.get('question', '')
    answer = None

    if question:
        # Step 1: Search Azure Cognitive Search
        search_params = {
            "api-version": "2021-04-30-Preview",
            "search": question,
            "queryType": "semantic",
            "semanticConfiguration": "default-semantic",
            "$top": 3
        }
        search_headers = {
            "api-key": search_api_key,
            "Content-Type": "application/json"
        }
        search_url = f"{search_endpoint}/indexes/{search_index}/docs"
        search_response = requests.get(search_url, params=search_params, headers=search_headers)
        docs = search_response.json().get('value', [])

        # Step 2: Build context from documents
        context = ""
        for i, doc in enumerate(docs, start=1):
            content = doc.get('content') or doc.get('content_text') or ""
            context += f"[Document {i}]\n{content}\n\n"

        # Step 3: Construct prompt
        prompt = f"""
You are a cybersecurity AI assistant helping to investigate an incident.
Use the following documents to answer the question. If the answer is not in the documents, say "I don't know".

Documents:
{context}
Question: {question}
Answer:
"""

        # Step 4: Call Azure OpenAI
        openai_url = f"{openai_endpoint}/openai/deployments/{openai_deployment}/completions?api-version=2022-12-01"
        openai_payload = {
            "prompt": prompt,
            "max_tokens": 400,
            "temperature": 0.2
        }
        openai_headers = {
            "api-key": openai_api_key,
            "Content-Type": "application/json"
        }
        openai_response = requests.post(openai_url, json=openai_payload, headers=openai_headers)
        answer = openai_response.json()['choices'][0]['text'].strip()

    return render_template_string(HTML_FORM, answer=answer)

if __name__ == '__main__':
    app.run(debug=True)
