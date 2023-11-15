import time
import numpy as np

from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)

from embedding import embed_attribute

HOST = "localhost"
PORT = "19530"
VECTOR_DIM = 768


def connect_server():
    print("Connecting to milvus...", end="")
    connections.connect("default", host=HOST, port=PORT)
    print("Success!")


def create_collection():
    print("Creating collection <data_model_embedding>...", end="")
    if utility.has_collection("data_model_embedding"):
        print("Collection <data_model_embedding> already exists!")
        return Collection("data_model_embedding")

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=50),
        FieldSchema(name="fields", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM)
    ]

    schema = CollectionSchema(fields, "Data model embedded by BERT")
    print("Success!")
    collection = Collection("data_model_embedding", schema, consistency_level="Strong")
    print("Creating index...", end="")
    index = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 16384},
    }
    collection.create_index("embedding", index)
    print("Success!")
    print("Loading...", end="")
    collection.load()
    print("Success!")
    return collection


def drop_collection():
    print("Dropping collection <data_model_embedding>...", end="")
    if utility.has_collection("data_model_embedding"):
        utility.drop_collection("data_model_embedding")
        print("Success!")


class MilvusDAO:
    def __init__(self):
        connect_server()
        self.collection = create_collection()

    def embed_model(self, model_id, fields, tags):
        tag_str = ', '.join(tags)
        field_str = ', '.join(fields)
        print(f"Embedding model '{model_id}' with field({field_str}) and tag({tag_str})...", end="")

        # Embedding strings by seperator
        # embedding = embed_attribute(field_str)

        # Embedding strings and count average
        embedding = np.stack([embed_attribute(field) for field in fields])
        embedding = np.mean(embedding, axis=0)

        self.collection.insert([[model_id], [field_str], [tag_str], [embedding]])
        print("Flushing...", end="")
        self.collection.flush()
        print("Success!")
        return True

    def query_models(self, fields, k=5):
        res = []
        field_str = ', '.join(fields)
        print(f"Querying models by field({field_str})...", end="")

        # Embedding strings by seperator
        # query_attribute = [embed_attribute(field_str)]

        # Embedding strings and count average
        query_attribute = np.stack([embed_attribute(field) for field in fields])
        query_attribute = [np.mean(query_attribute, axis=0)]

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 128},
        }
        start_time = time.time()
        result = self.collection.search(query_attribute, "embedding", search_params, limit=k,
                                        output_fields=["id", "fields", "tags"])
        end_time = time.time()
        print("Success! Query latency:{:.4f}s".format(end_time - start_time))
        for hits in result:
            for hit in hits:
                print(
                    f"Model: {hit.entity.get('id')}, Field:{hit.entity.get('fields')}, Tag: {hit.entity.get('tags')}, Distance: {hit.distance}")
                item = hit.entity.to_dict()['entity']
                item['fields'] = item['fields'].split(', ')
                item['tags'] = item['tags'].split(', ')
                res.append(item)
        return res

    # def insert_tag(self, tag):
    #     print(f"Inserting tag '{tag}'...", end="")
    #     if not self._has_redundant_tag(tag):
    #         embedding = embed_attribute(tag)
    #         self.collection.insert([[tag], [embedding]])
    #         print("Flushing...", end="")
    #         self.collection.flush()
    #         print("Success!")
    #         return True
    #     else:
    #         print("Failed! Redundant tag exists.")
    #         return False
    #
    # def insert_tags(self, tags):
    #     print(f"Inserting tags {tags}...", end="")
    #     tags = list(set(tags))
    #     if all(not self._has_redundant_tag(tag) for tag in tags):
    #         embeddings = [embed_attribute(tag) for tag in tags]
    #         self.collection.insert([tags, embeddings])
    #         print("Flushing...", end="")
    #         self.collection.flush()
    #         print("Success!")
    #         return True
    #     else:
    #         print("Failed! Redundant tag exists.")
    #         return False
    #
    # def delete_model(self, model_id):
    #     print(f"Deleting model '{model_id}'...", end="")
    #     expr = f"id in [\"{model_id}\"]"
    #     self.collection.delete(expr)
    #     print("Success!")
    #
    # def query_similar_tags(self, tag, k=3):
    #     res_tags = []
    #     print(f"Querying tag '{tag}'...", end="")
    #     query_attribute = [embed_attribute(tag)]
    #     search_params = {
    #         "metric_type": "L2",
    #         "params": {"nprobe": 10},
    #     }
    #     start_time = time.time()
    #     result = self.collection.search(query_attribute, "embedding", search_params, limit=k, output_fields=["tag"])
    #     end_time = time.time()
    #     print("Success! Search latency:{:.4f}s".format(end_time - start_time))
    #     for hits in result:
    #         for hit in hits:
    #             print(f"Tag: {hit.entity.get('tag')}, Distance: {hit.distance}")
    #             res_tags.append(hit.entity.get('tag'))
    #     return res_tags
    #
    # def _has_redundant_tag(self, tag):
    #     return len(self.collection.query(expr=f"tag == \"{tag}\"")) > 0

if __name__ == '__main__':
    pass