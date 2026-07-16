import copy
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool

from application.form_definitions import STRATEGY_FORM
from agents.setup_chat.common import SetupChatToolContext, build_args_schema


def get_strategy_tools() -> list[StructuredTool]:
    tools = []

    async def get_strategy_profile(config: RunnableConfig) -> dict[str, Any]:
        """Read the entire strategy profile including basic info and all form sections."""
        ctx: SetupChatToolContext = config["configurable"]["tool_context"]
        if not ctx.strategy_id:
            return {"error": "No strategy context provided."}
        
        strategy = await ctx.service.get_strategy(ctx.strategy_id)
        
        full_strategy_form = {}
        for section in STRATEGY_FORM.sections:
            val = strategy.sales_strategy_form.get(section.key, {})
            full_strategy_form[section.key] = val
            
        return {
            "identity": {
                "name": strategy.name,
                "target_companies": strategy.target_companies,
                "contacts_per_company_default": strategy.contacts_per_company_default,
            },
            "sales_strategy_form": full_strategy_form,
        }

    tools.append(
        StructuredTool.from_function(
            coroutine=get_strategy_profile,
            name="get_strategy_profile",
            description="Read the entire strategy profile including basic info and all form sections.",
        )
    )

    for section in STRATEGY_FORM.sections:
        key = section.key

        def _make_set(k: str, fields: tuple) -> StructuredTool:
            async def set_tool(config: RunnableConfig, **kwargs: Any) -> str:
                ctx: SetupChatToolContext = config["configurable"]["tool_context"]
                if ctx.mode == "chat":
                    return "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."
                
                if not ctx.strategy_id:
                    return "Error: No strategy context provided."
                
                updates = {key: val for key, val in kwargs.items() if val is not None}
                
                strategy = await ctx.service.get_strategy(ctx.strategy_id)
                current_form = copy.deepcopy(strategy.sales_strategy_form)
                
                # Unlike org and product, strategy identity is not a separate form section 
                # but run_targets/overview are parts of the form itself that also update the root model.
                # However, for consistency we can pass the name down to update_strategy_profile if overview.name is set
                
                section_data = current_form.get(k, {})
                if not isinstance(section_data, dict):
                    section_data = {}
                
                for field, value in updates.items():
                    section_data[field] = value
                current_form[k] = section_data
                
                name = None
                if k == "overview" and "name" in updates:
                    name = updates["name"]
                
                await ctx.service.update_strategy_profile(
                    ctx.strategy_id,
                    form=current_form,
                    name=name,
                )
                
                return f"Successfully saved strategy {k} section."

            doc = (
                f"Agent mode only. Update the strategy {k} section. "
                "Pass keys as arguments. Omitted keys are left unchanged. "
                "List keys replace the whole list. "
            )

            set_tool.__doc__ = doc

            schema = build_args_schema(k, fields)

            return StructuredTool.from_function(
                coroutine=set_tool,
                name=f"set_strategy_{k}",
                description=doc,
                args_schema=schema,
            )

        tools.append(_make_set(key, section.fields))

    return tools
