"""Notion MCP server — exposes Notion API operations as MCP tools."""

import os
from typing import Annotated

import httpx
from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("Notion")

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _headers() -> dict[str, str]:
    token = os.environ.get("NOTION_API_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _extract_title(page: dict) -> str:
    """Extract a readable title from a Notion page object."""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            return "".join(p.get("plain_text", "") for p in parts)
    return "Untitled"


def _extract_block_text(block: dict) -> str:
    """Extract plain text from a Notion block."""
    block_type = block.get("type", "")
    data = block.get(block_type, {})
    rich_text = data.get("rich_text", [])
    return "".join(part.get("plain_text", "") for part in rich_text)


@mcp.tool
async def search_pages(
    query: Annotated[str, Field(description="Search query to find Notion pages")],
) -> str:
    """Search for pages in the connected Notion workspace."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/search",
            headers=_headers(),
            json={
                "query": query,
                "filter": {"property": "object", "value": "page"},
                "page_size": 10,
            },
        )
        resp.raise_for_status()

    results = resp.json().get("results", [])
    if not results:
        return "No pages found."

    lines = []
    for page in results:
        title = _extract_title(page)
        page_id = page["id"]
        lines.append(f"- {title}  (id: {page_id})")
    return "\n".join(lines)


@mcp.tool
async def get_page_content(
    page_id: Annotated[str, Field(description="The Notion page ID to read")],
) -> str:
    """Get the text content of a Notion page."""
    blocks: list[dict] = []
    params: dict = {"page_size": 100}

    async with httpx.AsyncClient() as client:
        while True:
            resp = await client.get(
                f"{BASE_URL}/blocks/{page_id}/children",
                headers=_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            blocks.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            params["start_cursor"] = data["next_cursor"]

    if not blocks:
        return "Page is empty."

    lines = []
    for block in blocks:
        text = _extract_block_text(block)
        if text:
            lines.append(text)
    return "\n".join(lines) if lines else "Page has no readable text content."


@mcp.tool
async def create_page(
    parent_page_id: Annotated[str, Field(description="The parent page ID to create the new page under")],
    title: Annotated[str, Field(description="Title of the new page")],
    content: Annotated[str, Field(description="Text content for the page body")] = "",
) -> str:
    """Create a new page in Notion under a parent page."""
    children = []
    if content:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            },
        })

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/pages",
            headers=_headers(),
            json={
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "properties": {
                    "title": [{"type": "text", "text": {"content": title}}]
                },
                "children": children,
            },
        )
        resp.raise_for_status()

    page = resp.json()
    return f"Created page '{title}' with id: {page['id']}"


@mcp.tool
async def archive_page(
    page_id: Annotated[str, Field(description="The Notion page ID to archive")],
) -> str:
    """Archive (soft-delete) a Notion page."""
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{BASE_URL}/pages/{page_id}",
            headers=_headers(),
            json={"archived": True},
        )
        resp.raise_for_status()

    return f"Page {page_id} has been archived."


if __name__ == "__main__":
    mcp.run()
