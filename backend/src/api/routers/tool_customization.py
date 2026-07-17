from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.domain import (
    ToolCustomizationRuleCreate,
    ToolCustomizationRuleRead,
)
from persistence import models
from persistence.database import get_session

router = APIRouter(tags=["tool_customizations"])
Session = Annotated[AsyncSession, Depends(get_session)]

@router.get("/api/v1/tool-customizations", response_model=list[ToolCustomizationRuleRead])
async def get_public_tool_customizations(session: Session) -> object:
    return (await session.scalars(select(models.ToolCustomizationRule))).all()

@router.post("/api/v1/admin/tool-customizations", response_model=ToolCustomizationRuleRead)
async def create_tool_customization(data: ToolCustomizationRuleCreate, session: Session) -> object:
    existing = await session.scalar(
        select(models.ToolCustomizationRule).where(
            models.ToolCustomizationRule.tool_name_prefix == data.tool_name_prefix
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prefix already exists")
    
    row = models.ToolCustomizationRule(**data.model_dump())
    session.add(row)
    await session.commit()
    return row

@router.get("/api/v1/admin/tool-customizations", response_model=list[ToolCustomizationRuleRead])
async def get_tool_customizations(session: Session) -> object:
    return (await session.scalars(select(models.ToolCustomizationRule))).all()

@router.put("/api/v1/admin/tool-customizations/{rule_id}", response_model=ToolCustomizationRuleRead)
async def update_tool_customization(rule_id: str, data: ToolCustomizationRuleCreate, session: Session) -> object:
    row = await session.get(models.ToolCustomizationRule, rule_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    
    existing = await session.scalar(
        select(models.ToolCustomizationRule).where(
            models.ToolCustomizationRule.tool_name_prefix == data.tool_name_prefix,
            models.ToolCustomizationRule.id != rule_id
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prefix already exists")
    
    row.tool_name_prefix = data.tool_name_prefix
    row.icon_url = data.icon_url
    row.request_color = data.request_color
    row.response_color = data.response_color
    
    await session.commit()
    return row

@router.delete("/api/v1/admin/tool-customizations/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool_customization(rule_id: str, session: Session) -> None:
    row = await session.get(models.ToolCustomizationRule, rule_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    
    await session.delete(row)
    await session.commit()
