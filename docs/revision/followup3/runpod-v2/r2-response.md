# Runpod v2 port: response to review round 2 (Sol reject 0.98, Astra reject 0.98)

| # | Finding | Fix | Regression tests (fail on the r2 code) |
|---|---|---|---|
| D (Sol 1) | `GET /v2/pods` hides cluster member pods by default; reconcile and delete_verified could succeed while one lives | every page is `/pods?includeClusterPods=true`, later pages add `&cursor=<quoted, safe=''>` | `test_list_includes_cluster_pods_on_every_page` |
| E (Astra 1) | `urlopen` followed redirects, so a POST 302 then GET 404 was classified as a clear refusal | one opener with a redirect handler that returns None: a 3xx surfaces as an HTTPError with its own status (create: ambiguous; list: fails with no stdout); the balance call uses the same opener | real local HTTP server: `test_transport_never_follows_a_redirect` (301/302/303/307/308: one request, original status), `test_create_after_a_redirect_is_ambiguous_with_one_request` (301/302/303), `test_list_after_a_redirect_fails_with_no_stdout` (301/302/303) |

Suite: 120 passed (`test_runpod_v2.py`, `test_runpod.py`, `test_podctl.py`). Live read-only `list` `[]` exit 0; `balance` exit 0.
