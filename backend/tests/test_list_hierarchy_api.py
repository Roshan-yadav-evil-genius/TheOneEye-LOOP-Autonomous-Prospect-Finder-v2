from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from loop_testing.factories import organization_form, product_icp_form, sales_strategy_form
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from loop_api.main import create_app
from loop_api.persistence.database import Base, get_session


@pytest.fixture
async def client(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'list.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value
    await engine.dispose()


@pytest.mark.asyncio
async def test_list_organizations(client: AsyncClient) -> None:
    empty = await client.get("/api/v1/organizations")
    assert empty.status_code == 200
    assert empty.json() == []

    first = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Alpha Org",
            "website": "https://alpha.example",
            "org_form": organization_form(),
        },
    )
    second = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Beta Org",
            "website": "https://beta.example",
            "org_form": organization_form(),
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listed = await client.get("/api/v1/organizations")
    assert listed.status_code == 200
    names = [row["name"] for row in listed.json()]
    assert names == ["Beta Org", "Alpha Org"]


@pytest.mark.asyncio
async def test_list_products_and_strategies(client: AsyncClient) -> None:
    org = await client.post(
        "/api/v1/organizations",
        json={
            "name": "List Org",
            "website": "https://list.example",
            "org_form": organization_form(),
        },
    )
    assert org.status_code == 201
    org_id = org.json()["id"]
    validated = await client.post(f"/api/v1/organizations/{org_id}/profile/validate")
    assert validated.status_code == 200
    product = await client.post(
        f"/api/v1/organizations/{org_id}/products",
        json={"name": "List Product", "kind": "product", "icp_form": product_icp_form()},
    )
    assert product.status_code == 201
    product_id = product.json()["id"]
    product_ok = await client.post(f"/api/v1/products/{product_id}/profile/validate")
    assert product_ok.status_code == 200
    strategy = await client.post(
        f"/api/v1/products/{product_id}/sales-strategies",
        json={"sales_strategy_form": sales_strategy_form(name="List Strategy")},
    )
    assert strategy.status_code == 201

    products = await client.get(f"/api/v1/organizations/{org_id}/products")
    assert products.status_code == 200
    assert len(products.json()) == 1
    strategies = await client.get(f"/api/v1/products/{product_id}/sales-strategies")
    assert strategies.status_code == 200
    assert strategies.json()[0]["name"] == "List Strategy"
