# Python service for data management

A Python service used in [this project](https://github.com/1772692215/ist_data_management.git).

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

To configure the database profile, edit it in `config.py`:

```python
HOST = "localhost"
PORT = "19530"
```

You **don't** need to start the milvus database before you run this service.

To start the server, run:

```shell
python server.py
```

To init the database, run:

```shell
python init.py
```


To reset the database, run:

```shell
python reset.py
```

## APIs

### Embed model

```python
@app.route('/models', methods=['POST'])
def embed_model():
```

### Query similar models

```python
@app.route('/models', methods=['GET'])
def query_models():
```

### Query recommended tags

```python
@app.route('/models/tags', methods=['GET'])
def query_model_tags():
```