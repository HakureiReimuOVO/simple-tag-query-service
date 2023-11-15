from transformers import BertTokenizer, BertModel
import torch
import os

# Use domestic HuggingFace mirror site
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased', output_hidden_states=True)


def embed_attribute(attribute):
    tokens = tokenizer(attribute, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**tokens)

    # Apply BERT's [CLS] header output as embedding
    embeddings = outputs.last_hidden_state[:, 0, :].numpy().squeeze()

    return embeddings

#
# if __name__ == '__main__':
#     # text = 'Hello, how are you? My name is qianqidan. Can you tell me your name?'
#     text = ['Hello, how are you?', 'My name is qqd.', 'Can you tell me your name?']
#     embed = embed_attribute(text)
#     print(embed)
