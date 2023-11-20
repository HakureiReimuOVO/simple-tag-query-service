import numpy as np


def recommend_tags(models, tag_num=5):
    num_models = len(models)
    weights = [np.exp(-1 * i) for i in range(num_models)]
    model_tags = [model['tags'] for model in models]
    tag_weights = {}

    for i, tags in enumerate(model_tags):
        weight_per_tag = weights[i] / len(tags)
        for tag in tags:
            tag_weights[tag] = tag_weights.get(tag, 0) + weight_per_tag

    total_weight = sum(tag_weights.values())

    probabilities = [tag_weight / total_weight for tag_weight in tag_weights.values()]
    chosen_tags = np.random.choice(list(tag_weights.keys()),  min(len(tag_weights), tag_num), p=probabilities, replace=False)  # 假设最多推荐5个标签
    return list(chosen_tags)
