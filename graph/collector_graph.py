import logging
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from Data_base.db import get_profile_collection
from scrapers.run_scraper import run_all_sites
from Data_base.profile_repo import get_profile

logger = logging.getLogger(__name__)


# -------------------------
# 1) Define State
# -------------------------


class CollectorState(TypedDict):
    user_id: str
    queries: List[str]


# -------------------------
# 2) Define Nodes
# -------------------------


def load_profile_node(state: CollectorState):
    """
    Load profile from DB using user_id
    """
    user_id = state["user_id"]

    print(f"Loading profile for: {user_id}")

    profile = get_profile(user_id)

    if not profile:
        raise ValueError("Profile not found.")

    queries = profile.get("search_queries", [])

    print(f"Extracted queries: {queries}")

    state["queries"] = queries

    return state


# this is replaced by same one has collector status inside
# def run_scraper_node(state: CollectorState):
#     """
#     This node runs the scraping pipeline
#     """
#     queries = state["queries"]

#     print("Running collector with queries:", queries)

#     run_all_sites(queries)

#     return state


def run_scraper_node(state: CollectorState):
    user_id = state["user_id"]
    queries = state["queries"]

    try:
        print(f"[Collector] Started for {user_id}")

        # status = running
        get_profile_collection().update_one(
            {"user_id": user_id}, {"$set": {"collection_status": "running"}}
        )

        run_all_sites(queries)

        print(f"[Collector] Finished for {user_id}")

    except Exception as e:
        print(f"[Collector ERROR]: {e}")

    finally:
        # ALWAYS mark as done (even if error)
        get_profile_collection().update_one(
            {"user_id": user_id}, {"$set": {"collection_status": "done"}}
        )

    return state


# -------------------------
# 3) Build Graph
# -------------------------


def build_collector_graph():

    builder = StateGraph(CollectorState)

    builder.add_node("load_profile", load_profile_node)
    builder.add_node("run_scraper", run_scraper_node)

    builder.set_entry_point("load_profile")

    builder.add_edge("load_profile", "run_scraper")
    builder.add_edge("run_scraper", END)

    return builder.compile()


# Create compiled graph instance
collector_graph = build_collector_graph()
