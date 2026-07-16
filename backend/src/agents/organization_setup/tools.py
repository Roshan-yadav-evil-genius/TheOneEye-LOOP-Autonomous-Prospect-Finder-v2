import copy
from dataclasses import dataclass
from typing import Any, Literal, Type

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

from application.form_definitions import ORGANIZATION_FORM
from application.loop_service import LoopService


@dataclass
class OrgChatToolContext:
    organization_id: str
    mode: Literal["chat", "agent"]
    service: LoopService


def _build_args_schema(section_key: str, fields: tuple) -> Type[BaseModel]:
    annotations: dict[str, tuple[Type, Any]] = {}
    for f in fields:
        field_type = Any
        if f.kind in ("text", "textarea", "select"):
            field_type = str | None
        elif f.kind == "number":
            field_type = int | None
        elif f.kind == "boolean":
            field_type = bool | None
        elif f.kind in ("string-list", "multi-select"):
            field_type = list[str] | None
        elif f.kind == "object-list":
            field_type = list[dict[str, Any]] | None

        if f.path == ".":
            # root list field or object list
            # for unique_strengths, we will use 'strengths' as arg
            annotations["strengths"] = (list[str] | None, None)
        else:
            annotations[f.path.replace(".", "_")] = (field_type, None)

    return create_model(f"Set{section_key.title().replace('_', '')}Schema", **annotations)


def get_all_tools() -> list[StructuredTool]:
    tools = []

    async def get_org_profile(config: RunnableConfig) -> dict[str, Any]:
        """Read the entire organization profile including identity and all form sections."""
        ctx: OrgChatToolContext = config["configurable"]["tool_context"]
        org = await ctx.service.get_organization(ctx.organization_id)
        
        full_org_form = {}
        for section in ORGANIZATION_FORM.sections:
            val = org.org_form.get(section.key)
            if val is None:
                if section.key == "unique_strengths":
                    val = []
                else:
                    val = {}
            full_org_form[section.key] = val
            
        return {
            "identity": {
                "name": org.name,
                "website": org.website,
                "primary_contact_email": org.primary_contact_email,
            },
            "org_form": full_org_form,
        }

    tools.append(
        StructuredTool.from_function(
            coroutine=get_org_profile,
            name="get_organization_profile",
            description="Read the entire organization profile including identity and all form sections.",
        )
    )

    for section in ORGANIZATION_FORM.sections:
        key = section.key



        def _make_set(k: str, fields: tuple) -> StructuredTool:
            async def set_tool(config: RunnableConfig, **kwargs: Any) -> str:
                ctx: OrgChatToolContext = config["configurable"]["tool_context"]
                if ctx.mode == "chat":
                    return "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."
                
                # filter out None values to keep omitted fields unchanged
                updates = {key: val for key, val in kwargs.items() if val is not None}
                
                org = await ctx.service.get_organization(ctx.organization_id)
                current_form = copy.deepcopy(org.org_form)
                
                if k == "identity":
                    name = updates.get("name", org.name)
                    website = updates.get("website", org.website)
                    email = updates.get("primary_contact_email", org.primary_contact_email)
                    
                    await ctx.service.update_organization_profile(
                        ctx.organization_id,
                        form=current_form,
                        name=name,
                        website=str(website) if website else None,
                        primary_contact_email=email,
                    )
                else:
                    section_data = current_form.get(k, {})
                    if not isinstance(section_data, dict):
                        section_data = {}
                    
                    if "strengths" in updates and k == "unique_strengths":
                        # Special handling for unique_strengths which is just a list in org_form
                        current_form[k] = updates["strengths"]
                    else:
                        for field, value in updates.items():
                            section_data[field] = value
                        current_form[k] = section_data
                    
                    await ctx.service.update_organization_profile(
                        ctx.organization_id,
                        form=current_form,
                        name=org.name,
                        website=org.website,
                        primary_contact_email=org.primary_contact_email,
                    )
                
                return f"Successfully saved {k} section."

            doc = (
                f"Agent mode only. Update the {k} section. "
                "Pass keys as arguments. Omitted keys are left unchanged. "
                "List keys replace the whole list. "
            )
            if k == "unique_strengths":
                doc += "For unique_strengths, pass a single 'strengths' list argument."

            set_tool.__doc__ = doc

            schema = _build_args_schema(k, fields)

            return StructuredTool.from_function(
                coroutine=set_tool,
                name=f"set_{k}",
                description=doc,
                args_schema=schema,
            )

        tools.append(_make_set(key, section.fields))

    return tools
