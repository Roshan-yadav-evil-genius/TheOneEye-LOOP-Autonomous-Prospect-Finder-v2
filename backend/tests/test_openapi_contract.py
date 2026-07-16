"""OpenAPI contract presence checks — RecreationDocs 04-api-and-contracts.md."""

from loop_api.main import create_app

REQUIRED_PATHS = {
    "/api/v1/organizations",
    "/api/v1/organizations/{organization_id}/products",
    "/api/v1/products/{product_id}/sales-strategies",
    "/api/v1/sales-strategies/{strategy_id}/companies",
    "/api/v1/sales-strategies/{strategy_id}/companies/{company_id}/prospects",
    "/api/v1/sales-strategies/{strategy_id}/agents/{role}/start",
    "/api/v1/sales-strategies/{strategy_id}/agents/{role}/stop",
    "/api/v1/admin/dead-letters",
    "/api/v1/admin/jobs",
    "/health/live",
    "/health/ready",
}


def test_openapi_contains_required_operator_and_runtime_paths() -> None:
    schema = create_app().openapi()
    paths = set(schema["paths"])
    missing = REQUIRED_PATHS - paths
    assert not missing, f"Missing OpenAPI paths: {sorted(missing)}"


def test_metrics_endpoint_is_mounted() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"loop_http_requests_total" in response.content or response.content


def test_register_company_request_shape_matches_contracts() -> None:
    schema = create_app().openapi()
    body = schema["components"]["schemas"]["RegisterCompanyRequest"]
    assert set(body["required"]) == {"name", "website_url", "selection_reason"}
