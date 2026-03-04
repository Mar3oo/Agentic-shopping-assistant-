from agents.recommendation.embedding_model import get_embedding_model

model = get_embedding_model()

texts = ["Gaming laptop with RTX 4060", "Office laptop with long battery life"]

embeddings = model.encode(texts)

print("Shape:", embeddings.shape)
print("First vector sample:", embeddings[0][:5])
