from flask import Flask, jsonify, request
from dao import MilvusDAO

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
        k = int(data.get('k', 5))
        similar_models = milvus_dao.query_models_by_fields(fields=fields, k=k)
        return jsonify({'message': 'ok', 'code': 200, 'data': {'models': similar_models}})
    except Exception as e:
        return jsonify({'message': e, 'code': 400})


if __name__ == '__main__':
    milvus_dao = MilvusDAO()
    app.run()
