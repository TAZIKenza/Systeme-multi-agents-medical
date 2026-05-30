import httpx
import json
from typing import Any, Optional


MCP_SERVER_URL = "http://localhost:8001"


async def call_mcp_tool(tool_name: str, parameters: dict) -> Any:
    """
    Appelle un outil expose par le serveur MCP.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/{tool_name}",
                json=parameters
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {"error": f"Serveur MCP inaccessible sur {MCP_SERVER_URL}"}
    except Exception as e:
        return {"error": str(e)}


async def get_mcp_medical_context(symptoms: str) -> str:
    """
    Interroge le serveur MCP pour enrichir le contexte medical.
    """
    result = await call_mcp_tool("get_medical_context", {"symptoms": symptoms})
    if "error" in result:
        return f"Contexte MCP non disponible : {result['error']}"
    return result.get("context", "Aucun contexte supplementaire disponible.")


async def get_mcp_red_flags(symptoms: str) -> list:
    """
    Interroge le serveur MCP pour identifier les signaux d'alerte (red flags).
    """
    result = await call_mcp_tool("check_red_flags", {"symptoms": symptoms})
    if "error" in result:
        return []
    return result.get("red_flags", [])
