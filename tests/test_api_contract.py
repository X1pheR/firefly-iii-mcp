from firefly_iii_mcp.client import ALLOWED_ENDPOINTS, Endpoint

OFFICIAL_FIREFLY_VERSION = "6.6.6"
OFFICIAL_API_DOCS_BRANCH = "v6.6.6"
OFFICIAL_API_DOCS_REVISION = "fe6e96739ea9056c09d45e4fce1d471af23a2891"
EXPECTED_ENDPOINTS = {
    "/about",
    "/accounts",
    "/accounts/{id}",
    "/transactions",
    "/transactions/{id}",
    "/search/transactions",
    "/budgets",
    "/budget-limits",
    "/bills",
    "/categories",
    "/tags",
    "/piggy-banks",
    "/recurrences",
    "/currencies",
    "/rule-groups",
    "/rule-groups/{id}",
    "/rules",
    "/rules/{id}",
    "/exchange-rates/{from}/{to}",
    "/exchange-rates/{from}/{to}/{date}",
    "/summary/basic",
    "/insight/expense/total",
    "/insight/income/total",
    "/insight/transfer/total",
    "/insight/expense/category",
}


def test_endpoint_allowlist_matches_reviewed_firefly_6_6_6_contract() -> None:
    assert {endpoint.value for endpoint in ALLOWED_ENDPOINTS} == EXPECTED_ENDPOINTS
    assert len(Endpoint) == len(EXPECTED_ENDPOINTS)


def test_endpoint_allowlist_has_no_actions_exports_or_attachments() -> None:
    forbidden_fragments = ("export", "attachment", "/trigger", "/test", "import", "webhook", "cron", "data/")
    for path in EXPECTED_ENDPOINTS:
        assert not any(fragment in path for fragment in forbidden_fragments)
