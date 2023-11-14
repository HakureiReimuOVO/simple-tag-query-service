from flask import Flask, jsonify, request
# from dao import MilvusDAO
from llm import llm_exec

app = Flask(__name__)


@app.route('/insert', methods=['POST'])
def insert_tag():
    """
    Insert a tag into vector database.

    Request:
    - Method: POST
    - Content-Type: application/json
    - JSON Data:
        {
            "tag": <tag_to_insert (String)>
        }

    Returns:
    - 200 OK with JSON data: {'message': 'ok', 'code': 200, 'data': {'duplicated': <is_tag_duplicated (Boolean)>}}
    - 400 Bad Request with JSON data: {'message': <error_message (String)>, 'code': 400}
    """
    try:
        data = request.get_json()
        tag_to_insert = data['tag']
        duplicated = milvus_dao.insert_tag(tag=tag_to_insert)
        return jsonify({'message': 'ok', 'code': 200, 'data': {'duplicated': not duplicated}})
    except Exception as e:
        return jsonify({'message': e, 'code': 400}),


@app.route('/query', methods=['GET'])
def query_tags():
    """
    Query similar tags based on the provided 'tag'.

     Request:
     - Method: GET
     - Parameters:
        - tag: <tag_to_query>
        - k(optional): <num_of_result>

     Returns:
     - 200 OK with JSON data: {'message': 'ok', 'code': 200, 'data': {'tags': <similar_tags (List[String])>}}
     - 400 Bad Request with JSON data: {'message': <error_message (String), 'code': 400}
     """
    try:
        query_tag = request.args.get('tag')
        query_k = request.args.get('k', 5)
        similar_tags = milvus_dao.query_similar_tags(tag=query_tag, k=int(query_k))
    except Exception as e:
        return jsonify({'message': e, 'code': 400}),
    return jsonify({'message': 'ok', 'code': 200, 'data': {'tags': similar_tags}})


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
    - 200 OK with JSON data: {'message': 'ok', 'code': 200, 'data': {'LLM_answer': <LLM_returned_answer (String)>, "LLM_code": <LLM_returned_answer (String)>, "query_log": <completed_query_log>}}
    - 400 Bad Request with JSON data: {'message': <error_message (String)>, 'code': 400}
    '''
    try:
        data = request.get_json()
        ans, code, log = llm_exec.exec(data["demand"], data["domain"])
    except Exception as e:
        return jsonify({'message': e, 'code': 400}),
    return jsonify({'message': 'ok', 'code': 200, 'data': {"llmAnswer": ans, "llmCode": code, "queryLog": log}})
    

if __name__ == '__main__':
    # milvus_dao = MilvusDAO()
    app.run()