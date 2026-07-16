from dataclasses import dataclass
from typing import Any, Literal, Type
from pydantic import BaseModel, create_model

from application.loop_service import LoopService

@dataclass
class SetupChatToolContext:
    organization_id: str
    mode: Literal["chat", "agent"]
    service: LoopService
    product_id: str | None = None
    strategy_id: str | None = None

def build_args_schema(section_key: str, fields: tuple) -> Type[BaseModel]:
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
            # for unique_strengths or similar, use 'items' or specific name
            # since org tools uses 'strengths', we will use 'items' generically,
            # but wait, org_tools specifically expects 'strengths' for unique_strengths.
            # let's just keep 'strengths' for backward compatibility or make it generic 'items' and handle it per tool
            annotations["items"] = (list[Any] | None, None)
        else:
            annotations[f.path.replace(".", "_")] = (field_type, None)

    return create_model(f"Set{section_key.title().replace('_', '')}Schema", **annotations)
