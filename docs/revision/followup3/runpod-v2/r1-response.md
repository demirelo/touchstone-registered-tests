# Runpod v2 port: response to review round 1 (Sol reject 0.98, Astra reject 0.96; the same three points)

| # | Finding | Fix | Regression tests (fail on the r1 code: 12 of 12) |
|---|---|---|---|
| A (Sol 1, Astra 1) | A pod with a missing, null or non-string name passed the listing and would vanish from `podctl.named()` | `runpod.py` list: every pod, terminated or not, needs a non-empty string id and a string name, else the whole listing fails with no stdout | `test_list_rejects_a_pod_without_a_string_id_and_name` (6 cases) |
| B (Sol 2, Astra 2) | A numeric body `error` bypassed the status guard: 202 `{"id": q, "error": 400}` returned q as a pod; 200/201 `{"error": 400}` was unambiguous; numeric ids were accepted | `create_one.py` classifies by HTTP status: only 201 with a non-empty string id is a pod; a status of 400 or more goes to the r11 rule (`classify_creation({"error": status})`); everything else is ambiguous | `test_create_classifies_by_http_status` (11 cases) |
| C (Sol 3, Astra 3) | `hasNextPage: false` ended the listing without checking `nextCursor` | the final page needs `hasNextPage` exactly false and `nextCursor` present and null; a further page needs `hasNextPage` true and a non-empty string cursor; anything else fails with no stdout, on any page | `test_list_rejects_inconsistent_pagination` (7), `test_list_rejects_a_bad_later_page` |

Suite: `test_runpod_v2.py`, `test_runpod.py`, `test_podctl.py`: 108 passed. Live read-only `runpod.py list`: `[]`, exit 0.
