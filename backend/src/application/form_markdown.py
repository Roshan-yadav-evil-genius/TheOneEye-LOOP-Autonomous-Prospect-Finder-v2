"""Render offline markdown worksheets from canonical form definitions."""

from __future__ import annotations

from application.form_definitions import FORM_TEMPLATES, FormFieldDef, FormTemplateDef


def _required_suffix(required: bool) -> str:
    return " *(required)*" if required else ""


def _placeholder_for(field: FormFieldDef) -> str:
    match field.kind:
        case "textarea":
            return "_Enter your answer here (multiple lines)._"
        case "number":
            return "_Enter a number._"
        case "boolean":
            return "- [ ] Yes\n- [ ] No"
        case "string-list":
            return "- \n- \n- "
        case "select":
            options = "\n".join(f"- {option}" for option in field.options)
            return f"_Choose one:_\n{options}\n\n**Your choice:**"
        case "multi-select":
            options = "\n".join(f"- [ ] {option}" for option in field.options)
            return f"_Select all that apply:_\n{options}\n\n**Also list any custom entries below:**\n- "
        case "object-list":
            blocks = []
            for item_field in field.item_fields:
                blocks.append(
                    f"**{item_field.label}**{_required_suffix(item_field.required)}\n"
                    f"_{item_field.help or 'Enter value.'}_\n\n"
                    f"{_placeholder_for(item_field)}\n"
                )
            return "\n".join(blocks) + "\n\n_Duplicate this block for each additional item._"
        case _:
            return "_Enter your answer here._"


def _field_block(field: FormFieldDef) -> str:
    lines = [
        f"#### {field.label}{_required_suffix(field.required)}",
        "",
        f"**Purpose:** {field.help or 'Provide the requested information.'}",
    ]
    if field.avoid:
        lines.extend(["", f"**Do not enter:** {field.avoid}"])
    lines.extend(["", "**Your answer:**", "", _placeholder_for(field), ""])
    return "\n".join(lines)


def render_form_markdown(template: FormTemplateDef) -> str:
    lines = [
        f"# {template.title} — Offline Worksheet",
        "",
        "> Fill this form offline and return it to your operator. "
        "They will enter your answers into the LOOP portal.",
        "",
        "## About this form",
        "",
        template.purpose,
        "",
        "## Instructions",
        "",
        "### What to provide",
        "",
    ]
    lines.extend(f"- {item}" for item in template.provide_guidance)
    lines.extend(["", "### What NOT to enter", ""])
    lines.extend(f"- {item}" for item in template.avoid_guidance)
    lines.append("")
    lines.append("---")
    lines.append("")

    for index, section in enumerate(template.sections, start=1):
        lines.extend(
            [
                f"## {index}. {section.title}",
                "",
                f"_{section.help}_",
                "",
            ]
        )
        for field in section.fields:
            lines.append(_field_block(field))
        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "## Submission",
            "",
            "When complete, send this file back to your operator. "
            "They will review and enter the data into the portal.",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_for_form(form_key: str) -> tuple[str, str]:
    template = FORM_TEMPLATES[form_key]
    return template.filename, render_form_markdown(template)
