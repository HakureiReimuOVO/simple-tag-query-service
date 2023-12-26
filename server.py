import os

# Use domestic HuggingFace mirror site
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from flask import Flask, jsonify, request
from dao import MilvusDAO
from service import recommend_tags

app = Flask(__name__)


@app.route('/models', methods=['POST'])
def embed_model():
    try:
        data = request.get_json()
        milvus_dao.embed_model(**data)
        return jsonify({'message': 'ok', 'code': 200})
    except Exception as e:
        return jsonify({'message': e, 'code': 400}),


@app.route('/models', methods=['GET'])
def query_models():
    try:
        data = request.args
        fields = data.get('fields').split(',')
        model_num = int(data.get('model_num', 5))
        similar_models = milvus_dao.query_models_by_fields(fields=fields, model_num=model_num)
        return jsonify({'message': 'ok', 'code': 200, 'data': {'models': similar_models}})
    except Exception as e:
        return jsonify({'message': e, 'code': 400})


@app.route('/models/tags', methods=['GET'])
def query_model_tags():
    try:
        data = request.args
        fields = data.get('fields').split(',')
        model_num = int(data.get('model_num', 10))
        tag_num = int(data.get('tag_num', 5))
        similar_models = milvus_dao.query_models_by_fields(fields=fields, model_num=model_num)
        filtered_similar_models = list(filter(lambda model: model['tags'] and model['tags'] != [''], similar_models))
        tags = recommend_tags(models=filtered_similar_models, tag_num=tag_num)
        return jsonify({'message': 'ok', 'code': 200, 'data': {'tags': tags}})
    except Exception as e:
        return jsonify({'message': e, 'code': 400})


if __name__ == '__main__':
    milvus_dao = MilvusDAO()
    app.run(host='0.0.0.0', port=5000)
