import requests

response = requests.post(
    "http://localhost:8000/api/upload_corpus",
    json={"corpus_name": "test", "text": "example sample test"}
)

print(response.status_code)
print(response.text)