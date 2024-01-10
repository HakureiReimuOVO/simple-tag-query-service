from flask import Flask, jsonify, request
from dao import MilvusDAO
from service import recommend_tags
from llm import llm_exec

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
        model_num = int(data.get('model_num', 5))
        tag_num = int(data.get('tag_num', 5))
        similar_models = milvus_dao.query_models_by_fields(fields=fields, model_num=model_num)
        tags = recommend_tags(models=similar_models, tag_num=tag_num)
        return jsonify({'message': 'ok', 'code': 200, 'data': {'tags': tags}})
    except Exception as e:
        return jsonify({'message': e, 'code': 400})


@app.route('/llm', methods=['POST'])
def llm_interaction():
    '''
    interaction with LLM.

    Request:
    - Method: POST
    - Content-Type: application/json
    - JSON Data:
        {
            "demand": <demand_to_LLM (String)>
            "domain": <LLM_code_used_in (String)>
        }

    Returns:
    - 200 OK with JSON data: {'message': 'ok', 'code': 200, 'data': {'LLM_answer': <LLM_returned_answer (String)>, "LLM_code": <LLM_returned_answer (String)>, "query_log": <completed_query_log>, "executeResult": <sqlcode_executed_result>}}
    - 400 Bad Request with JSON data: {'message': <error_message (String)>, 'code': 400}
    '''
    try:
        data = request.get_json()
        ans, out_code, log, executeResult = llm_exec.exec(data["demand"], data["domain"])
    except Exception as e:
        return jsonify({'message': e, 'code': 500}),
    return jsonify({'message': 'ok', 'code': 200, 'data': {"llmAnswer": ans, "llmCode": out_code, "queryLog": log, "executeResult": executeResult}})
    

if __name__ == '__main__':
    milvus_dao = MilvusDAO()
    app.run()
