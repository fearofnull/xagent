# -*- coding: utf-8 -*-
# flake8: noqa: E501
# pylint: disable=line-too-long
"""The Cron API tool for managing cron jobs via HTTP API."""

import json
from typing import Optional

import httpx
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from ...constant import WEB_ADMIN_URL, WEB_ADMIN_TOKEN


async def call_cron_api(
    action: str,
    job_id: Optional[str] = None,
    job_spec: Optional[str] = None,
) -> ToolResponse:
    """Call the Cron API to manage cron jobs.

    This tool provides a way to interact with the Web Admin's Cron API
    without depending on hardcoded file system paths or CLI commands.

    Args:
        action (`str`):
            The action to perform. Valid actions:
            - "list": List all cron jobs
            - "get": Get a specific cron job (requires job_id)
            - "create": Create a new cron job (requires job_spec)
            - "update": Update an existing cron job (requires job_id and job_spec)
            - "delete": Delete a cron job (requires job_id)
            - "pause": Pause a cron job (requires job_id)
            - "resume": Resume a cron job (requires job_id)
            - "run": Run a cron job immediately (requires job_id)
        job_id (`Optional[str]`, defaults to `None`):
            The ID of the cron job (required for get, update, delete, pause, resume, run actions).
        job_spec (`Optional[str]`, defaults to `None`):
            The job specification as a JSON string (required for create and update actions).

    Returns:
        `ToolResponse`:
            The tool response containing the API response data or error message.
    """

    # Get configuration from constants
    base_url = WEB_ADMIN_URL
    token = WEB_ADMIN_TOKEN

    # Validate action
    valid_actions = ["list", "get", "create", "update", "delete", "pause", "resume", "run"]
    if action not in valid_actions:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Invalid action '{action}'. Valid actions are: {', '.join(valid_actions)}",
                ),
            ],
        )

    # Validate required parameters
    if action in ["get", "update", "delete", "pause", "resume", "run"] and not job_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: job_id is required for action '{action}'",
                ),
            ],
        )

    if action in ["create", "update"] and not job_spec:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: job_spec is required for action '{action}'",
                ),
            ],
        )

    # Parse job_spec if provided
    spec_data = None
    if job_spec:
        try:
            spec_data = json.loads(job_spec)
            
            # Transform simplified format to full CronJobSpec format
            if action == "create" and spec_data:
                # Extract simplified parameters
                job_type = spec_data.get("type", "text")
                job_name = spec_data.get("name", "Unnamed Job")
                job_id = spec_data.get("id")
                cron_expr = spec_data.get("cron", "0 0 * * *")
                channel = spec_data.get("channel", "feishu")
                target_user = spec_data.get("target_user")
                target_chat = spec_data.get("target_chat")
                target_session = spec_data.get("target_session")  # Legacy support
                text = spec_data.get("text", "")
                enabled = spec_data.get("enabled", True)
                timezone = spec_data.get("timezone", "UTC")
                
                # Use target_chat if provided, otherwise use target_session (legacy), otherwise use target_user
                chat_id = target_chat or target_session
                user_id = target_user
                
                # Build full CronJobSpec format
                spec_data = {
                    "id": job_id,
                    "name": job_name,
                    "enabled": enabled,
                    "schedule": {
                        "type": "cron",
                        "cron": cron_expr,
                        "timezone": timezone
                    },
                    "task_type": job_type,
                    "text": text if job_type == "text" else None,
                    "request": {
                        "input": [
                            {
                                "role": "user",
                                "type": "text",
                                "content": [{"text": text}]
                            }
                        ],
                        "session_id": None,
                        "user_id": "cron"
                    } if job_type == "agent" else None,
                    "dispatch": {
                        "type": "channel",
                        "channel": channel,
                        "target": {
                            "chat_id": chat_id,
                            "user_id": user_id
                        },
                        "mode": "final",
                        "meta": {}
                    },
                    "runtime": {
                        "max_concurrency": 1,
                        "timeout_seconds": 120,
                        "misfire_grace_seconds": 60
                    },
                    "meta": {}
                }
        except json.JSONDecodeError as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Invalid JSON in job_spec: {e}",
                    ),
                ],
            )

    # Build the API endpoint and HTTP method
    endpoint = f"{base_url}/api/cron/jobs"
    method = "GET"
    json_data = None

    if action == "list":
        method = "GET"
    elif action == "get":
        endpoint = f"{endpoint}/{job_id}"
        method = "GET"
    elif action == "create":
        method = "POST"
        json_data = spec_data
    elif action == "update":
        endpoint = f"{endpoint}/{job_id}"
        method = "PUT"
        json_data = spec_data
    elif action == "delete":
        endpoint = f"{endpoint}/{job_id}"
        method = "DELETE"
    elif action == "pause":
        endpoint = f"{endpoint}/{job_id}/pause"
        method = "POST"
    elif action == "resume":
        endpoint = f"{endpoint}/{job_id}/resume"
        method = "POST"
    elif action == "run":
        endpoint = f"{endpoint}/{job_id}/run"
        method = "POST"

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Make the HTTP request
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(endpoint, headers=headers)
            elif method == "POST":
                response = await client.post(endpoint, headers=headers, json=json_data)
            elif method == "PUT":
                response = await client.put(endpoint, headers=headers, json=json_data)
            elif method == "DELETE":
                response = await client.delete(endpoint, headers=headers)

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    error_code = error_data.get("error", {}).get("code", "UNKNOWN")
                    return ToolResponse(
                        content=[
                            TextBlock(
                                type="text",
                                text=f"Error: API request failed with status {response.status_code}\nCode: {error_code}\nMessage: {error_msg}",
                            ),
                        ],
                    )
                except json.JSONDecodeError:
                    return ToolResponse(
                        content=[
                            TextBlock(
                                type="text",
                                text=f"Error: API request failed with status {response.status_code}\n{response.text}",
                            ),
                        ],
                    )

            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Error: Failed to parse API response as JSON: {e}\n{response.text}",
                        ),
                    ],
                )

            # Format the response in a human-friendly way
            if result.get("success"):
                if action == "list":
                    jobs = result.get("data", [])
                    if not jobs:
                        response_text = "No cron jobs found."
                    else:
                        job_lines = []
                        for job in jobs:
                            status = "enabled" if job.get("enabled") else "disabled"
                            job_lines.append(
                                f"- {job.get('id')}: {job.get('name')} ({status})"
                            )
                        response_text = f"Found {len(jobs)} cron job(s):\n" + "\n".join(job_lines)
                elif action == "get":
                    data = result.get("data", {})
                    spec = data.get("spec", {})
                    state = data.get("state", {})
                    response_text = f"Job: {spec.get('name')}\n"
                    response_text += f"ID: {spec.get('id')}\n"
                    response_text += f"Status: {'enabled' if spec.get('enabled') else 'disabled'}\n"
                    response_text += f"Schedule: {spec.get('schedule', {}).get('cron', 'N/A')}\n"
                    response_text += f"Task Type: {spec.get('task_type')}\n"
                    if state:
                        response_text += f"Last Run: {state.get('last_run_at', 'Never')}\n"
                        response_text += f"Next Run: {state.get('next_run_at', 'N/A')}\n"
                        response_text += f"Last Status: {state.get('last_status', 'N/A')}"
                elif action == "create":
                    data = result.get("data", {})
                    response_text = f"Successfully created cron job: {data.get('name')} (ID: {data.get('id')})"
                elif action == "update":
                    data = result.get("data", {})
                    response_text = f"Successfully updated cron job: {data.get('name')} (ID: {data.get('id')})"
                elif action == "delete":
                    response_text = result.get("message", "Job deleted successfully")
                elif action == "pause":
                    response_text = result.get("message", "Job paused successfully")
                elif action == "resume":
                    response_text = result.get("message", "Job resumed successfully")
                elif action == "run":
                    response_text = result.get("message", "Job started successfully")
                else:
                    response_text = json.dumps(result, indent=2)

                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=response_text,
                        ),
                    ],
                )
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Error: {error_msg}",
                        ),
                    ],
                )

    except httpx.ConnectError as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Failed to connect to Web Admin at {base_url}. Please ensure the Web Admin service is running.\nDetails: {e}",
                ),
            ],
        )
    except httpx.TimeoutException as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Request to Web Admin timed out after 30 seconds.\nDetails: {e}",
                ),
            ],
        )
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Unexpected error occurred while calling Cron API: {e}",
                ),
            ],
        )
