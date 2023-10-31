# A simple milvus service for tag similarity search

A simple service used in [this project](https://github.com/1772692215/ist_data_management.git).

- Database: [milvus](https://milvus.io)
- Service port: 5000
- Dependency:

```
Flask==2.2.3
numpy==1.21.4
numpy==1.21.2
pymilvus==2.3.1
torch==1.10.0
transformers==4.30.2
```


## Usage

To configure the database profile, edit it in **dao.py**:

```python
HOST = "localhost"
PORT = "19530"
```

You **don't** need to start the milvus database before you run this service.

To start the server, run:

```shell
python server.py
```

To reset the database, run:

```shell
python reset.py
```

## APIs

### Insert new tag

```python
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
```

### Query similar tags

```python
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
```