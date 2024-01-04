from flask import Flask, request, jsonify
import os
import sys
import time
import constants
from langchain.document_loaders import TextLoader 
from langchain.indexes import VectorstoreIndexCreator
from langchain.llms import openai
from langchain.chat_models import ChatOpenAI
import json
import re
import requests

app = Flask(__name__)

VIDEO_API_KEY = "OTczZjE0MTExMWQ4NGZmMWIzZTFhOTFmMDBmZmNlY2MtMTY5OTU1OTM3NA=="


def query_desc_test(prompt): 
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_d.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    output = index.query(prompt, llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return output

def query_outcomes_test(prompt):
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_o.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    desc = query_desc_test(prompt)
    output = index.query(prompt + "learning_description:" + desc, llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return [output,desc]

def query_outline_test(prompt):
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_outline.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    outcomes = query_outcomes_test(prompt)
    output = index.query(prompt + "learning_description:" + outcomes[0] + "learning outcomes" + outcomes[1] , llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return [output,outcomes[0],outcomes[1]]

def clean_json_data(json_data):
    # Remove non-printable characters using a regular expression
    cleaned_data = re.sub(r'\\\\\[\\\\x00-\\\\x1F\\\\x7F-\\\\x9F\]', '', json_data)
    return cleaned_data

@app.route("/", methods=['GET'])
def read_root():
    return {"message": "Welcome to the video generation API"}

@app.route("/generate_desc", methods=['POST'])
def query_desc():
    query = request.json['text'] 
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_d.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    output = index.query(query, llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return output

@app.route("/generate_outcomes", methods=['POST'])
def query_outcomes():
    query = request.json['text'] 
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_o.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    desc = query_desc_test(query)
    output = index.query(query + "learning_description:" + desc, llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return [output,desc]

@app.route("/generate_outline", methods=['POST'])
def query_outline():
    query = request.json['text'] 
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_outline.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    outcomes = query_outcomes_test(query)
    output = index.query(query + "learning_description:" + outcomes[0] + "learning outcomes" + outcomes[1] , llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return output

@app.route("/generate_script", methods=['POST'])
def query_script():
    query = request.json['text'] 
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('learning_script.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    outline = query_outline_test(query)
    output = index.query(query + "learning_description:" + outline[2] + "learning outcomes" + outline[1] + "outline: " +  outline[0], llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    print(output)
    # cleaned_json_data = clean_json_data(output)
    # data_new = json.loads(cleaned_json_data)
    return [output, outline[2], outline[1], outline[0]]

@app.route("/generate_text", methods=['POST'])
def query_index():
    query = request.json['text'] 
    os.environ["OPENAI_API_KEY"] = constants.APIKEY
    loader = TextLoader('data.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    output = index.query(query, llm=ChatOpenAI(model='gpt-3.5-turbo', temperature=0))
    cleaned_json_data = clean_json_data(output)
    data_new = json.loads(cleaned_json_data)
    return jsonify(data_new)

def get_video_status(video_id):
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {
        "X-Api-Key": VIDEO_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        json_data = response.json()
    except requests.RequestException as err:
        return jsonify({"status": "error", "message": str(err)})
    
    data = {
        "status": "undefined" 
    }

    if "data" in json_data:
        status = json_data["data"].get("status")
        if status == "completed":
            data["status"] = "completed"
            data["video_url"] = json_data["data"].get("video_url") 
        elif status == "processing" or status == "pending":
            data["status"] = "processing"
        else:
            data["status"] = "error"
            data["message"] = json_data.get("message")

    else:
        data["status"] = "error"
        data["message"] = "invalid response"

    return jsonify(data)

def generate_video(text):
    url = "https://api.heygen.com/v1/video.generate"
    headers = {
        "X-Api-Key": VIDEO_API_KEY,
        "Content-Type": "application/json" 
    }
    
    data = {
        "background": "#ffffff",
        "clips": [{
            "avatar_id": "Daisy-inskirt-20220818",
            "avatar_style": "normal", 
            "input_text": text,
            "offset": {"x": 0, "y": 0}, 
            "scale": 1,
            "voice_id": "1bd001e7e50f421d891986aad5158bc8"
        }],
        "ratio": "16:9",
        "test": True,
        "version": "v1alpha"
    }
    
    response = requests.post(url, json=data, headers=headers)
    data = response.json()
    return data

@app.route("/generate_video", methods=['POST'])
def generate():
    prompt = request.json['text']
    
    try:
        response = generate_video(prompt)
        return jsonify(response)
    except:
        return jsonify({"error": "Request failed"})
    
@app.route("/status", methods=['POST'])  
def get_status():
    video_id = request.json['id']
    
    try:
        status = get_video_status(video_id)
        return status
    except:
        return jsonify({"error": "Failed to get status"})

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=8080)