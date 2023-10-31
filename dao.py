import time

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
    print("Creating collection <tag_embeddings>...", end="")
    if utility.has_collection("tag_embeddings"):
        print("Collection <tag_embeddings> already exists!")
        return Collection("tag_embeddings")

    fields = [
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="tag", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM)
    ]

    schema = CollectionSchema(fields, "Tag with its embedding value output by BERT")
    print("Success!")
    collection = Collection("tag_embeddings", schema, consistency_level="Strong")
    print("Creating index...", end="")
    index = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128},
    }
    collection.create_index("embedding", index)
    print("Success!")
    print("Loading...", end="")
    collection.load()
    print("Success!")
    return collection


def drop_collection():
    print("Dropping collection <tag_embeddings>...", end="")
    if utility.has_collection("tag_embeddings"):
        utility.drop_collection("tag_embeddings")
        print("Success!")


class MilvusDAO:
    def __init__(self):
        connect_server()
        self.collection = create_collection()

    def insert_tag(self, tag):
        print(f"Inserting tag '{tag}'...", end="")
        if not self._has_redundant_tag(tag):
            embedding = embed_attribute(tag)
            self.collection.insert([[tag], [embedding]])
            print("Flushing...", end="")
            self.collection.flush()
            print("Success!")
            return True
        else:
            print("Failed! Redundant tag exists.")
            return False

    def insert_tags(self, tags):
        print(f"Inserting tags {tags}...", end="")
        tags = list(set(tags))
        if all(not self._has_redundant_tag(tag) for tag in tags):
            embeddings = [embed_attribute(tag) for tag in tags]
            self.collection.insert([tags, embeddings])
            print("Flushing...", end="")
            self.collection.flush()
            print("Success!")
            return True
        else:
            print("Failed! Redundant tag exists.")
            return False

    def delete_pk(self, pk):
        print(f"Deleting pk '{pk}'...", end="")
        expr = f"pk in [\"{pk}\"]"
        self.collection.delete(expr)
        print("Success!")

    def query_similar_tags(self, tag, k=3):
        res_tags = []
        print(f"Querying tag '{tag}'...", end="")
        query_attribute = [embed_attribute(tag)]
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }
        start_time = time.time()
        result = self.collection.search(query_attribute, "embedding", search_params, limit=k, output_fields=["tag"])
        end_time = time.time()
        print("Success! Search latency:{:.4f}s".format(end_time - start_time))
        for hits in result:
            for hit in hits:
                print(f"Tag: {hit.entity.get('tag')}, Distance: {hit.distance}")
                res_tags.append(hit.entity.get('tag'))
        return res_tags

    def _has_redundant_tag(self, tag):
        return len(self.collection.query(expr=f"tag == \"{tag}\"")) > 0


if __name__ == "__main__":
    dao = MilvusDAO()

