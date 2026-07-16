import copy
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool

from application.form_definitions import PRODUCT_FORM
from agents.setup_chat.common import SetupChatToolContext, build_args_schema


def get_product_tools() -> list[StructuredTool]:
    tools = []

    async def get_product_profile(config: RunnableConfig) -> dict[str, Any]:
        """Read the entire product profile including basic info and all form sections."""
        ctx: SetupChatToolContext = config["configurable"]["tool_context"]
        if not ctx.product_id:
            return {"error": "No product context provided."}
        
        product = await ctx.service.get_product(ctx.product_id)
        
        full_product_form = {}
        for section in PRODUCT_FORM.sections:
            val = product.icp_form.get(section.key)
            if val is None:
                if section.key == "customer_success_stories":
                    val = []
                else:
                    val = {}
            full_product_form[section.key] = val
            
        return {
            "identity": {
                "name": product.name,
                "kind": product.kind,
            },
            "icp_form": full_product_form,
        }

    tools.append(
        StructuredTool.from_function(
            coroutine=get_product_profile,
            name="get_product_profile",
            description="Read the entire product profile including basic info and all form sections.",
        )
    )

    for section in PRODUCT_FORM.sections:
        key = section.key

        def _make_set(k: str, fields: tuple) -> StructuredTool:
            async def set_tool(config: RunnableConfig, **kwargs: Any) -> str:
                ctx: SetupChatToolContext = config["configurable"]["tool_context"]
                if ctx.mode == "chat":
                    return "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."
                
                if not ctx.product_id:
                    return "Error: No product context provided."
                
                updates = {key: val for key, val in kwargs.items() if val is not None}
                
                product = await ctx.service.get_product(ctx.product_id)
                current_form = copy.deepcopy(product.icp_form)
                
                if k == "identity":
                    name = updates.get("name", product.name)
                    kind = updates.get("kind", product.kind)
                    
                    await ctx.service.update_product_profile(
                        ctx.product_id,
                        form=current_form,
                        name=name,
                        kind=kind,
                    )
                else:
                    section_data = current_form.get(k, {})
                    if not isinstance(section_data, dict) and k != "customer_success_stories":
                        section_data = {}
                    
                    if k == "customer_success_stories" and "items" in updates:
                        current_form[k] = updates["items"]
                    else:
                        for field, value in updates.items():
                            section_data[field] = value
                        current_form[k] = section_data
                    
                    await ctx.service.update_product_profile(
                        ctx.product_id,
                        form=current_form,
                        name=product.name,
                        kind=product.kind,
                    )
                
                return f"Successfully saved product {k} section."

            doc = (
                f"Agent mode only. Update the product {k} section. "
                "Pass keys as arguments. Omitted keys are left unchanged. "
                "List keys replace the whole list. "
            )

            set_tool.__doc__ = doc

            schema = build_args_schema(k, fields)

            return StructuredTool.from_function(
                coroutine=set_tool,
                name=f"set_product_{k}",
                description=doc,
                args_schema=schema,
            )

        tools.append(_make_set(key, section.fields))

    return tools
