from search_pipeline.pipeline import SearchPipeline


# optional: reuse instance (faster)
pipeline = SearchPipeline()


def run_search(message: str):
    try:
        products = pipeline.run(query=message, search_limit=10, top_k=5)

        return {
            "status": "success",
            "type": "search",
            "message": "Here are live search results",
            "data": {"products": products},
        }

    except Exception as e:
        return {"status": "error", "type": "search", "message": str(e), "data": {}}
