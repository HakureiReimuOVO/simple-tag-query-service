from flask import Flask, jsonify, request
from dao import MilvusDAO

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
        - tag: <tag_to_query (String)>

     Returns:
     - 200 OK with JSON data: {'message': 'ok', 'code': 200, 'data': {'tags': <similar_tags (List[String])>}}
     - 400 Bad Request with JSON data: {'message': <error_message (String), 'code': 400}
     """
    try:
        query_tag = request.args.get('tag')
        similar_tags = milvus_dao.query_similar_tags(tag=query_tag)
    except Exception as e:
        return jsonify({'message': e, 'code': 400}),
    return jsonify({'message': 'ok', 'code': 200, 'data': {'tags': similar_tags}})


if __name__ == '__main__':
    milvus_dao = MilvusDAO()
    app.run()
