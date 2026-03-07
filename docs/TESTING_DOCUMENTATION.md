# Agentic Shopping Assistant - System Analysis and Testing Documentation

## 1) Objective
This document provides a practical testing baseline for the current codebase:
- System architecture and runtime flow
- Current technical risks and blockers
- Test strategy (unit, integration, end-to-end)
- Concrete test scenarios with expected results
- Test execution plan and exit criteria

Analysis date: 2026-03-06

## 2) Scope and Components
Main components discovered in the repository:
- `main.py`: CLI orchestrator for profile collection, scraping trigger, recommendation, and feedback.
- `agents/profile/*`: LLM profile extraction and query generation.
- `graph/collector_graph.py`: LangGraph flow for loading profile and running scraping pipeline.
- `scrapers/*`: Amazon/Noon/Jumia Selenium scraping and normalization.
- `Data_base/*`: MongoDB connection, profile/feedback repositories, ingestion.
- `agents/recommendation/*`: Embedding retrieval, BM25, scoring, LLM reranking, recommendation chat handling.
- `agents/reviews/*`: YouTube review fetch + sentiment analysis.
- `tools/*`: Product type classifier, DB reset helper.

## 3) Runtime Flow (As Implemented)
1. User starts CLI chat in `main.py`.
2. Profile agent collects structured profile and search queries.
3. Profile is saved in MongoDB (`user_profiles`).
4. Cache check decides whether scraping is needed.
5. If needed, collector graph runs scrapers and ingestion.
6. Recommendation agent retrieves products, scores, reranks, and returns top products.
7. User feedback is stored in `user_feedback`.
8. Recommendation chat mode supports budget/brand refinements, explanations, comparison, and review sentiment.

## 4) Data Model (Observed)
Collections:
- `products_raw`:
  - `metadata`: `source`, `scraped_at`, `search_query`, `page_number`
  - `product`: `title`, `price`, `link`, `details_text`, `seller_score`, `category`, `product_type`, `embedding`
- `user_profiles`:
  - `user_id`
  - `profile` object from profile agent
  - optional `collection_status`
- `user_feedback`:
  - `user_id`, `product_link`, `liked`, `timestamp`

## 5) Critical Findings (Testing Blockers and High Risks)

### P0 - Must be addressed before reliable end-to-end testing
1. **Import-time DB connection side effect**
   - `Data_base/db.py:99-100` initializes `user_profiles` and `products_raw` at module import time.
   - This makes importing modules fail when DB/network is unavailable, blocking isolated tests.

2. **Missing symbol import in main entrypoint**
   - `main.py:10` imports `detect_product_type` from `agents/recommendation/agent.py`, but no such function exists there.
   - Expected behavior: use `classify_product_type` from `tools/product_classifier.py` or implement the missing function.

3. **Profile schema mismatch between profile and recommendation pipeline**
   - Profile schema fields: `product_category`, `product_intent`, `budget` (`agents/profile/schemas.py`).
   - Recommendation expects: `category`, `use_case`, `budget_min`, `budget_max` (`agents/recommendation/agent.py`, `main.py`).
   - Result: recommendation can receive empty/invalid criteria.

4. **Incorrect product type classification call**
   - `agents/recommendation/agent.py:73` passes full `profile` dict into `classify_product_type`, but classifier expects text (`tools/product_classifier.py`).
   - This can produce runtime errors or invalid type classification.

5. **Scraping scope artificially limited**
   - Pagination loops stop at one page:
     - `scrapers/amazon.py:78`
     - `scrapers/jumia.py:73`
     - `scrapers/noon.py:75`
   - Query loop currently processes only first query:
     - `scrapers/run_scraper.py:195` uses `SEARCH_QUERIES[:1]`
   - Test outcomes will not represent full production behavior.

6. **Thread safety issue in scraper enrichment**
   - `scrapers/run_scraper.py:143` uses `ThreadPoolExecutor` with one shared Selenium driver object.
   - Selenium WebDriver is not thread-safe; this can cause flaky tests and nondeterministic failures.

### P1 - Important quality and reliability issues
1. **Recommendation feedback hardcoded to one user**
   - `agents/recommendation/scorer.py` calls `get_user_feedback("user_005")`.
   - Multi-user scenarios cannot be validated correctly.

2. **Potential index error when no recommendations exist**
   - `agents/recommendation/chat_handler.py:111` reads `current_recommendations[0]` without empty-list guard.

3. **Intent mismatch**
   - Chat handler supports `review_sentiment`, but intent prompt in `agents/recommendation/prompts.py` does not list it.
   - Routing may never intentionally select that branch.

4. **Missing dependencies in `requirements.txt`**
   - Code imports include packages not listed explicitly: `sentence-transformers`, `faiss` (`faiss-cpu`), `rank-bm25`, `google-api-python-client`, `youtube-transcript-api`, `numpy`.
   - Fresh environment setup may fail.

5. **Main session reset behavior**
   - `main.py` deletes profile for `user_005` on each run.
   - This affects repeatability assumptions for long-running and regression tests.

## 6) Test Strategy

### Stage A - Pre-test stabilization (required)
Complete these fixes/config updates before full testing:
1. Remove import-time DB collection initialization side effects.
2. Fix missing `detect_product_type` reference.
3. Unify profile schema contract between profile and recommendation layers.
4. Remove first-query/first-page hard limits, or make them explicit flags.
5. Replace threaded single-driver enrichment with safe sequential flow or one-driver-per-thread model.
6. Complete `requirements.txt`.

### Stage B - Unit testing (fast, isolated)
Target pure logic and mock external services:
- `tools/product_classifier.py`
- `Data_base/ingestion.py` normalization and validation helpers
- `agents/recommendation/scorer.py` scoring functions
- intent router JSON fallback behavior
- product normalization in `scrapers/*.py`

Use:
- `pytest`
- `pytest-mock`
- deterministic fixtures

### Stage C - Integration testing (with test DB and mocked APIs)
Cover module contracts:
- Profile save/read (`profile_repo`)
- Ingestion upsert behavior and dedupe by `product.link`
- Collector graph state transitions (`collection_status`)
- Recommendation retrieval + ranking against seeded products

Use:
- dedicated Mongo test database
- mocked LLM/API calls (Groq, YouTube)

### Stage D - End-to-end testing
User journey tests:
1. Discovery mode profile completion
2. Scraping trigger and ingestion summary
3. Recommendation output quality and stability
4. Refinement commands (`budget`, `brand`, `compare`, `review`)
5. Feedback persistence and next recommendation impact

## 7) Suggested Test Matrix

| ID | Type | Component | Scenario | Expected Result |
|---|---|---|---|---|
| U01 | Unit | Classifier | classify known laptop text | returns expected product type |
| U02 | Unit | Classifier | empty input | returns `other` |
| U03 | Unit | Ingestion | invalid missing link | record counted as `failed` |
| U04 | Unit | Ingestion | string price with currency | normalized to float |
| U05 | Unit | Ingestion | URL with query params | normalized canonical link |
| U06 | Unit | Scorer | no user budget | neutral price scoring applied |
| U07 | Unit | Scorer | seller score normalization | output in [0,1] |
| U08 | Unit | Router | malformed JSON response | fallback to `general_question` |
| U09 | Unit | Amazon normalize | ASIN URL canonicalization | stable `/dp/{asin}` link |
| U10 | Unit | Jumia normalize | percent seller score | normalized to 0..1 |
| I01 | Integration | Profile repo | save then get profile | returned profile equals input |
| I02 | Integration | Ingestion + DB | insert then reinsert same link | first inserted, second updated |
| I03 | Integration | Product cache | enough products in range | returns `True` |
| I04 | Integration | Collector graph | run with valid profile | status transitions to `done` |
| I05 | Integration | Recommendation | seeded products + profile | non-empty ranked list |
| I06 | Integration | Feedback | save feedback then score | liked product gets boost |
| E01 | E2E | Main flow | complete profile to recommendations | user gets top recommendations |
| E02 | E2E | Refinement | user changes budget | recommendation set updates |
| E03 | E2E | Compare | compare command with valid indices | returns comparison text |
| E04 | E2E | New search | new search intent | returns to discovery mode |

## 8) Non-functional Testing
- Reliability: scraper retries and timeout behavior.
- Performance:
  - ingestion throughput per 100 records
  - recommendation latency with 1k, 10k, 50k products
- Data quality:
  - duplicate rate by normalized link
  - embedding availability ratio
- Resilience:
  - DB unavailable at startup
  - API key missing (`GROQ_API_KEY`, `YOUTUBE_API_KEY`)
  - scraper site structure changes

## 9) Test Environment and Configuration
Required env vars:
- `MONGO_URI_CLOUD`
- `GROQ_API_KEY`
- `YOUTUBE_API_KEY` (needed for review analysis path)

Recommended:
- Separate test Mongo database
- Deterministic seed dataset
- Mock external API clients by default in CI

## 10) Execution Plan
1. Apply Stage A stabilization fixes.
2. Add baseline unit tests for ingestion, classifier, scorer, and normalizers.
3. Add integration suite with seeded Mongo test DB.
4. Add smoke E2E flow for happy path.
5. Add regression suite for discovered defects.

## 11) Quality Gates (Exit Criteria)
Minimum release gate:
- 100% pass on critical unit tests (ingestion, classifier, scorer)
- 100% pass on integration tests for profile/ingestion/recommendation path
- 1 stable E2E happy-path pass
- no open P0 defects
- documented fallback behavior for missing APIs/keys

## 12) Immediate Next Implementation Tasks (Recommended)
1. Refactor DB module to lazy-load collections only when functions are called.
2. Create a profile contract mapper:
   - `product_category -> category`
   - `product_intent -> use_case`
   - `budget (string) -> budget_min/budget_max`
3. Replace `detect_product_type` import or implement it.
4. Add a `SCRAPER_LIMITS` config so test mode vs full mode is explicit.
5. Remove shared-driver multithreading in enrichment.
6. Add missing packages to `requirements.txt`.
7. Create `tests/` with initial `pytest` suite from matrix above.
