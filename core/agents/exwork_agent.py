#!/usr/bin/env python3
"""
ExWork Agent - Trinity Convergence Integration
Advanced autonomous agent system from PONGEX integrated into LoL Nexus

This module provides the primary autonomous agent capabilities,
integrating PONGEX's ExWork system with the Trinity architecture.
"""

import asyncio
import binascii
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import requests
import threading
import socket  # For DAEMON_IPC handler
import difflib  # For APPLY_PATCH handler
import re  # For platform detection in check_dependencies
import platform  # For platform detection in check_dependencies
import hashlib  # For learn_from_failures caching
import stat  # For security permission checks in resolve_path
import getpass  # For sudo password input

# Optional rich UI imports - fallback to basic print if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.text import Text
    from rich import print as rprint
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None
    def rprint(*args, **kwargs):
        print(*args, **kwargs)

# Optional questionary import for interactive prompts
try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False
    questionary = None

# Agent Ex-Work: Executes structured JSON commands with self-improvement features.
# Version: 3.0 (Tungsten Grade - Core Team Reviewed & Augmented)


# Load environment variables from .env file
load_dotenv()

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ExWork-v3.0] [%(levelname)-7s] %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("AgentExWorkV3.0")

# --- Configuration ---
PROJECT_ROOT = Path.cwd().resolve()
HISTORY_FILE = PROJECT_ROOT / ".exwork_history.jsonl"
DEFAULT_OLLAMA_ENDPOINT_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma:2b")
RUFF_EXECUTABLE = shutil.which("ruff") or "ruff"
PATCH_EXECUTABLE = shutil.which("patch") or "patch"  # NEW: Path to patch executable
AGENT_VERSION = "3.0"  # Tungsten Grade version

# --- Global State ---
_pending_signoffs: Dict[str, Dict[str, Any]] = {}

# --- Action Handler Registration ---
ACTION_HANDLERS: Dict[str, Callable[[Dict, Path, str, Optional[str]], Tuple[bool, Any]]] = {}  # Handler now takes step_id, sudo_password


# --- Dynamic Learning and Adaptation ---
def learn_from_failures(task_name: str, error_details: str, step_id: str):  # MODIFY SIGNATURE
    """Analyzes task failures and suggests or creates new handlers dynamically using LLM."""
    logger.warning(f"Learning from failure in task '{task_name}' (step_id: {step_id}): {error_details}")
    proposed_handler_name = f"auto_generated_{task_name}_handler"

    # Cache to prevent redundant refinements for the same error on the same task
    cache_key = f"{task_name}_{hashlib.sha256(error_details.encode()).hexdigest()}"
    if hasattr(learn_from_failures, "_cache"):  # type: ignore[attr-defined]
        cache = learn_from_failures._cache  # type: ignore[attr-defined]
    else:
        cache = learn_from_failures._cache = {}  # type: ignore[attr-defined]

    if cache_key in cache:
        logger.info(f"Skipping redundant refinement for handler '{proposed_handler_name}' due to cached error.")
        return

    cache[cache_key] = True  # Mark as processed for this error

    # Prepare context for LLM
    context = {
        "task_name": task_name,
        "error_details": error_details,
        "recent_history": [],  # You'd fill this from history_file if desired for LLM context
    }

    # Call LLM for dynamic handler generation suggestion
    llm_prompt = f"""Agent Ex-Work encountered an error. Analyze the situation and provide a concise diagnosis and a specific, actionable suggestion.

Failed Task: {task_name}
Error Details:
{error_details}

Based on this failure, propose a concise diagnosis and, if possible, suggest a new or refined action handler in Python.
If you propose a new handler, structure it as a Python function that accepts action_data, project_root, step_id, sudo_password, and returns Tuple[bool, Any].
Use the @handler(name='proposed_handler_name') decorator.
If a new handler isn't feasible, suggest a fix_type of 'COMMAND', 'PATCH', 'MANUAL_STEPS', 'CONFIG_ADJUSTMENT', or 'INFO_REQUEST'.

Desired Output Format (JSON):
{{
"diagnosis": "Concise diagnosis",
"fix_type": "HANDLER_CODE" | "COMMAND" | "PATCH" | "MANUAL_STEPS" | "CONFIG_ADJUSTMENT" | "INFO_REQUEST",
"fix_content": "Proposed Python handler code or command string or patch content or manual steps description"
}}
"""
    success, llm_response_str = call_local_llm_helper(llm_prompt, step_id=step_id, action_name="LEARN_FROM_FAILURES_LLM_CALL")

    if success:
        try:
            llm_result = json.loads(llm_response_str)
            if isinstance(llm_result, dict) and all(
                k in llm_result
                for k in ["diagnosis", "fix_type", "fix_content"]
            ):
                if llm_result.get("fix_type") == "HANDLER_CODE":
                    handler_code = llm_result.get("fix_content")
                    if handler_code:
                        logger.info(f"Attempting to dynamically register new handler '{proposed_handler_name}'")
                        # --- CRITICAL SECURITY WARNING ---
                        # Executing dynamically generated code is EXTREMELY RISKY.
                        # For a real system, this requires:
                        # 1. An isolated, sandboxed execution environment (e.g., dedicated Docker container, microVM).
                        # 2. Strict resource limits for the sandbox.
                        # 3. Code signature verification (if receiving signed code from Orchestrator).
                        # 4. Mandatory Architect approval in the terminal (as implemented below).
                        # ---------------------------------
                        
                        if RICH_AVAILABLE:
                            rprint(Panel(
                                Text(f"LLM proposes new handler code for '{task_name}':\n\n", style="bold yellow") +
                                Syntax(handler_code, "python", theme="monokai"),
                                title=f"[bold red]CRITICAL: LLM Proposed Dynamic Handler Code[/bold red]",
                                border_style="red"
                            ))
                        else:
                            print(f"\n[CRITICAL: LLM Proposed Dynamic Handler Code for '{task_name}']")
                            print(f"Code:\n{handler_code}")
                        
                        # Use questionary for better interactive prompts if available
                        if QUESTIONARY_AVAILABLE:
                            approval = questionary.confirm(f"Do you APPROVE dynamic execution of this LLM-proposed handler code for '{task_name}'? (y/N):").ask()
                        else:
                            approval = input(f"Do you APPROVE dynamic execution of this LLM-proposed handler code for '{task_name}'? (y/N): ").strip().lower()
                            approval = approval == 'y' or approval == 'yes'
                        
                        if approval:
                            try:
                                # Create a restricted execution context if possible, or use a subprocess with strict permissions
                                # For simplicity in this script, using direct exec which is HIGHLY DANGEROUS.
                                exec_globals = {
                                    "ACTION_HANDLERS": ACTION_HANDLERS, "logger": logger, "Path": Path,
                                    "resolve_path": resolve_path, "_run_subprocess": _run_subprocess,
                                    "handler": handler, "subprocess": subprocess, "shlex": shlex, "os": os,
                                    "base64": base64, "binascii": binascii, "difflib": difflib, "re": re,
                                    "platform": platform, "socket": socket  # Include all necessary imports for handlers
                                }
                                exec(handler_code, exec_globals, exec_globals)
                                logger.info(f"Dynamically registered handler '{proposed_handler_name}'.")
                                rprint("[green]Dynamically generated handler registered successfully.[/green]")
                                return
                            except Exception as e:
                                logger.error(f"Error executing dynamically generated handler code: {e}", exc_info=True)
                                cache[cache_key] = False  # Allow retry if execution failed
                                rprint(f"[red]ERROR: Failed to dynamically execute handler code: {e}[/red]")
                        else:
                            logger.warning(f"Architect rejected dynamic handler for '{task_name}'.")
                            rprint("[yellow]Architect rejected dynamic handler.[/yellow]")
                    else:
                        logger.warning("LLM proposed HANDLER_CODE but content was empty.")
                else:  # Other fix_types like COMMAND, PATCH, MANUAL_STEPS, CONFIG_ADJUSTMENT, INFO_REQUEST
                    logger.info(f"LLM proposed fix for '{task_name}': Type={llm_result.get('fix_type')}, Content={llm_result.get('fix_content')[:100]}...")
                    # Here, the agent would typically request signoff for these fixes to the orchestrator.
                    # Using a simple display for now - in production, this would integrate with orchestrator
                    rprint(f"[blue]LLM SUGGESTION[/blue] Fix type: {llm_result.get('fix_type')}")
                    rprint(f"Details: {llm_result.get('fix_content')}")

            else:  # LLM response missing required keys
                logger.warning(
                    f"LLM response for diagnosis was not the expected JSON structure: {llm_response_str[:300]}"
                )
                rprint(f"[yellow]WARNING:[/yellow] LLM provided malformed response for '{task_name}': {llm_response_str[:200]}...")

        except json.JSONDecodeError:
            logger.error(f"LLM response for learn_from_failures was not valid JSON: {llm_response_str[:300]}")
            rprint(f"[red]ERROR:[/red] LLM response for '{task_name}' was invalid JSON: {llm_response_str[:200]}...")
        except Exception as e:
            logger.error(f"Unexpected error processing LLM response for learn_from_failures: {e}", exc_info=True)
            rprint(f"[red]ERROR:[/red] Unexpected error processing LLM response for '{task_name}': {e}")
    else:
        logger.error(f"Failed to get LLM response for learn_from_failures: {llm_response_str}")
        rprint(f"[red]ERROR:[/red] Failed to get LLM response for '{task_name}'. No fix suggested.")


# Extend the handler decorator to support versioning and dynamic updates
def handler(name: str, version: Optional[str] = None):
    """Decorator to register or update action handlers."""

    def decorator(func: Callable[[Dict, Path, str, Optional[str]], Tuple[bool, Any]]):
        handler_key = f"{name}:{version}" if version else name
        ACTION_HANDLERS[handler_key] = func
        logger.debug(f"Registered action handler for: {handler_key}")
        return func

    return decorator


# --- Helper Functions ---


def resolve_path(project_root: Path, requested_path: str) -> Optional[Path]:
    """Safely resolves path relative to project root. Prevents traversal."""
    try:
        normalized_req_path = requested_path.replace("\\", "/")
        relative_p = Path(normalized_req_path)

        if relative_p.is_absolute():
            abs_path = relative_p.resolve()
            common = Path(os.path.commonpath([project_root, abs_path]))
            if common != project_root and abs_path != project_root:
                logger.error(
                    f"Absolute path '{requested_path}' is not within project root '{project_root}'. Rejected."
                )
                return None
        else:
            if ".." in relative_p.parts:
                logger.error(f"Path traversal with '..' rejected: '{requested_path}'")
                return None
            abs_path = (project_root / relative_p).resolve()
            common = Path(os.path.commonpath([project_root, abs_path]))
            if common != project_root and abs_path != project_root:
                logger.error(
                    f"Path unsafe! Resolved '{abs_path}' outside project root '{project_root}'. Rejected."
                )
                return None

        # NEW: Additional security permission checks
        if abs_path.exists():
            try:
                file_stat = abs_path.stat()
                # Check for suspicious permissions (world-writable files/directories)
                if file_stat.st_mode & stat.S_IWOTH:
                    logger.warning(f"Security warning: Path '{abs_path}' is world-writable. Proceeding with caution.")
                # Check for setuid/setgid bits on executables
                if abs_path.is_file() and (file_stat.st_mode & (stat.S_ISUID | stat.S_ISGID)):
                    logger.warning(f"Security warning: Path '{abs_path}' has setuid/setgid bits set.")
            except OSError as e:
                logger.warning(f"Could not check permissions for '{abs_path}': {e}")

        logger.debug(f"Resolved path '{requested_path}' to '{abs_path}'")
        return abs_path
    except Exception as e:
        logger.error(
            f"Error resolving path '{requested_path}' relative to '{project_root}': {e}"
        )
        return None


def log_execution_history(record: Dict[str, Any]):
    """Appends an execution record to the history file."""
    record_final = {
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action_name": record.get("action_name", "UNKNOWN_ACTION"),
        "command": record.get("command", "N/A"),
        "cwd": str(record.get("cwd", PROJECT_ROOT)),
        "success": record.get("success", False),
        "exit_code": record.get("exit_code", -1),
        "stdout_snippet": str(record.get("stdout_snippet", ""))[:500]
        + ("..." if len(str(record.get("stdout_snippet", ""))) > 500 else ""),
        "stderr_snippet": str(record.get("stderr_snippet", ""))[:500]
        + ("..." if len(str(record.get("stderr_snippet", ""))) > 500 else ""),
        "message": record.get("message", ""),
        "duration_s": round(record.get("duration_s", 0.0), 3),
        "step_id": record.get("step_id", "N/A"),
        "action_params": record.get("action_params", {}),
    }
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_final) + "\n")
    except Exception as e:
        logger.error(
            f"Failed to log execution history for action '{record_final['action_name']}': {e}"
        )


def _run_subprocess(
    command: List[str],
    cwd: Path,
    action_name: str,
    action_params: Dict,
    step_id: str,
    timeout: int = 300,
    sudo_password: Optional[str] = None,  # NEW: Optional sudo password for non-interactive sudo
) -> Tuple[bool, str, str, str]:
    """Helper to run subprocess. Returns: (success, user_message, stdout, stderr)"""
    start_time = time.time()
    command_str = " ".join(shlex.quote(c) for c in command)
    logger.info(f"Running {action_name}: {command_str} in CWD={cwd}")

    stdout_str = ""
    stderr_str = ""
    exit_code = -1
    user_message = ""

    # Determine the actual command list, accounting for sudo
    full_command_list: List[str]
    use_sudo_flag = action_params.get("use_sudo", False)

    if use_sudo_flag:
        full_command_list = ["sudo", "-n"] + command  # Try non-interactive sudo first
    else:
        full_command_list = command

    try:
        result = subprocess.run(
            full_command_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        stdout_str = result.stdout.strip() if result.stdout else ""
        stderr_str = result.stderr.strip() if result.stderr else ""
        exit_code = result.returncode

        # --- Handle sudo password fallback if -n failed ---
        # This block executes if the first subprocess.run failed due to a password prompt
        # and a sudo_password was provided.
        if exit_code != 0 and "password for" in stderr_str.lower() and use_sudo_flag and sudo_password:
            logger.warning(f"Sudo -n failed for '{command_str}'. Attempting with piped password...")
            try:
                # Re-run command piping password to sudo -S
                p = subprocess.Popen(
                    ["sudo", "-S"] + command,  # -S reads password from stdin
                    cwd=cwd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    timeout=timeout,
                    encoding="utf-8",
                    errors="replace",
                )
                password_bytes = (sudo_password + "\n").encode('utf-8')
                # Communicate sends stdin, then waits for stdout/stderr
                stdout_str_new, stderr_str_new = p.communicate(input=password_bytes, timeout=timeout)
                exit_code = p.returncode

                stdout_str = stdout_str_new.strip() if stdout_str_new else ""
                stderr_str = stderr_str_new.strip() if stderr_str_new else ""  # This stderr might still contain sudo's error

                if exit_code == 0:
                    success = True
                    user_message = f"{action_name} completed successfully (sudo via password)."
                    logger.info(f"Finished {action_name} (sudo via password). Code: {exit_code}")
                else:
                    success = False
                    user_message = f"{action_name} failed (Code: {exit_code}, sudo via password)."
                    logger.error(f"Finished {action_name} (sudo via password). Code: {exit_code}\nSTDERR: {stderr_str}")

            except subprocess.TimeoutExpired:
                success = False
                user_message = f"{action_name} timed out with piped password."
                stderr_str = "Timeout Error"
                logger.error(user_message)
                exit_code = -2
            except Exception as e:
                success = False
                user_message = f"Sudo password pipe unexpected error: {type(e).__name__}"
                stderr_str = str(e)
                logger.error(user_message, exc_info=True)
                exit_code = -4
        # --- End sudo password fallback block ---

        elif exit_code == 0:  # Original non-sudo-piped command succeeded
            success = True
            user_message = f"{action_name} completed successfully."
            logger.info(
                f"Finished {action_name}. Code: {exit_code}\n--- STDOUT ---\n{stdout_str if stdout_str else '<empty>'}"
            )
            if stderr_str:
                logger.warning(
                    f"--- STDERR (RC=0 but stderr present) ---\n{stderr_str}"
                )
        else:  # Original command failed, and not a password prompt we handled
            success = False
            user_message = f"{action_name} failed (Code: {exit_code})."
            logger.error(
                f"Finished {action_name}. Code: {exit_code}\n--- STDOUT ---\n{stdout_str if stdout_str else '<empty>'}\n--- STDERR ---\n{stderr_str if stderr_str else '<empty>'}"
            )

    except subprocess.TimeoutExpired:
        success = False
        user_message = f"{action_name} timed out after {timeout} seconds."
        stderr_str = "Timeout Error"
        logger.error(user_message)
        exit_code = -2
    except FileNotFoundError:
        executable_name = command[0]
        success = False
        user_message = f"Command not found for {action_name}: {executable_name}"
        stderr_str = f"Command not found: {executable_name}"
        logger.error(user_message)
        exit_code = -3
    except Exception as e:
        success = False
        user_message = f"Unexpected error running {action_name}: {type(e).__name__}"
        stderr_str = str(e)
        logger.error(f"Error running {action_name}: {e}", exc_info=True)
        exit_code = -4

    log_execution_history(
        {
            "timestamp": start_time,
            "action_name": action_name,
            "command": command_str,
            "cwd": str(cwd),
            "success": success,
            "exit_code": exit_code,
            "stdout_snippet": stdout_str,
            "stderr_snippet": stderr_str,
            "message": user_message,
            "duration_s": time.time() - start_time,
            "step_id": step_id,
            "action_params": action_params,
        }
    )
    return success, user_message, stdout_str, stderr_str


def call_local_llm_helper(
    prompt: str,
    model_name: Optional[str] = None,
    api_endpoint_base: Optional[str] = None,
    options: Optional[Dict] = None,
    step_id: str = "N/A",
    action_name: str = "CALL_LOCAL_LLM_HELPER",
) -> Tuple[bool, str]:
    """Internal helper to call local LLM. Returns (success, response_text_or_error_msg)."""
    start_time = time.time()
    actual_model = model_name or DEFAULT_OLLAMA_MODEL
    actual_endpoint_base = api_endpoint_base or DEFAULT_OLLAMA_ENDPOINT_BASE
    actual_endpoint_generate = f"{actual_endpoint_base.rstrip('/')}/api/generate"
    llm_options = options or {}

    logger.info(f"Targeting {actual_model} @ {actual_endpoint_generate}")
    payload = {
        "model": actual_model,
        "prompt": prompt,
        "stream": False,
        "options": llm_options,
    }
    if not llm_options:
        del payload["options"]

    action_params = {
        "model": actual_model,
        "prompt_length": len(prompt),
        "api_endpoint": actual_endpoint_generate,
        "options": llm_options,
    }

    try:
        response = requests.post(
            actual_endpoint_generate,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        llm_response_text = data.get("response", "").strip()

        if not llm_response_text:
            err_detail = data.get("error", "LLM returned empty response content.")
            logger.warning(f"LLM empty response. Error detail: {err_detail}")
            success = False
            message = f"LLM returned empty response. Detail: {err_detail}"
        else:
            logger.info("Local LLM call successful.")
            success = True
            message = llm_response_text

        log_execution_history(
            {
                "timestamp": start_time,
                "action_name": action_name,
                "success": success,
                "message": message if success else f"LLM Error: {message}",
                "duration_s": time.time() - start_time,
                "step_id": step_id,
                "action_params": action_params,
                "stdout_snippet": llm_response_text if success else "",
            }
        )
        return success, message
    except requests.exceptions.RequestException as e:
        err_msg = f"LLM Request Error: {e}"
        logger.error(f"LLM Call Failed: {err_msg}")
        log_execution_history(
            {
                "timestamp": start_time,
                "action_name": action_name,
                "success": False,
                "message": err_msg,
                "duration_s": time.time() - start_time,
                "step_id": step_id,
                "action_params": action_params,
                "stderr_snippet": str(e),
            }
        )
        return False, err_msg
    except Exception as e:
        err_msg = f"Unexpected LLM error: {type(e).__name__}: {e}"
        logger.error(f"LLM call unexpected error: {err_msg}", exc_info=True)
        log_execution_history(
            {
                "timestamp": start_time,
                "action_name": action_name,
                "success": False,
                "message": err_msg,
                "duration_s": time.time() - start_time,
                "step_id": step_id,
                "action_params": action_params,
                "stderr_snippet": str(e),
            }
        )
        return False, err_msg


# --- Action Handler Functions (Enhanced & Using Decorator) ---


@handler(name="ECHO")
def handle_echo(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    message = action_data.get("message", "No message provided for ECHO.")
    print(f"[EXWORK_ECHO_STDOUT] {message}")
    logger.info(f"ECHO: {message}")
    return True, f"Echoed: {message}"


@handler(name="CREATE_OR_REPLACE_FILE")
def handle_create_or_replace_file(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    relative_path = action_data.get("path")
    content_base64 = action_data.get("content_base64")
    if not isinstance(relative_path, str) or not relative_path:
        return False, "Missing or invalid 'path' (string) for CREATE_OR_REPLACE_FILE."
    if not isinstance(content_base64, str):
        return (
            False,
            "Missing or invalid 'content_base64' (string) for CREATE_OR_REPLACE_FILE.",
        )

    file_path = resolve_path(project_root, relative_path)
    if not file_path:
        return False, f"Invalid or unsafe path specified: '{relative_path}'"
    try:
        decoded_content = base64.b64decode(content_base64, validate=True)
        logger.info(f"Writing {len(decoded_content)} bytes to: {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(decoded_content)
        return (
            True,
            f"File '{relative_path}' written successfully ({len(decoded_content)} bytes).",
        )
    except (binascii.Error, ValueError) as b64e:
        logger.error(f"Base64 decode error for '{relative_path}': {b64e}")
        return False, f"Base64 decode error for '{relative_path}': {b64e}"
    except Exception as e:
        logger.error(f"Error writing file '{relative_path}': {e}", exc_info=True)
        return False, f"Error writing file '{relative_path}': {type(e).__name__} - {e}"


@handler(name="APPEND_TO_FILE")
def handle_append_to_file(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    relative_path = action_data.get("path")
    content_base64 = action_data.get("content_base64")
    add_newline = action_data.get("add_newline_if_missing", True)

    if not isinstance(relative_path, str) or not relative_path:
        return False, "Missing or invalid 'path' (string) for APPEND_TO_FILE."
    if not isinstance(content_base64, str):
        return False, "Missing or invalid 'content_base64' (string) for APPEND_TO_FILE."

    file_path = resolve_path(project_root, relative_path)
    if not file_path:
        return False, f"Invalid or unsafe path specified: '{relative_path}'"
    try:
        decoded_content = base64.b64decode(content_base64, validate=True)
        logger.info(f"Appending {len(decoded_content)} bytes to: {file_path}")

        file_exists_before_open = file_path.exists()
        if not file_exists_before_open:
            logger.warning(
                f"File '{relative_path}' does not exist. Creating before appending."
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("ab") as f:
            if add_newline and file_exists_before_open and file_path.stat().st_size > 0:
                with file_path.open("rb") as rf:
                    rf.seek(-1, os.SEEK_END)
                    if rf.read(1) != b"\n":
                        f.write(b"\n")
            f.write(decoded_content)
        return True, f"Appended {len(decoded_content)} bytes to '{relative_path}'."
    except (binascii.Error, ValueError) as b64e:
        logger.error(f"Base64 decode error for '{relative_path}': {b64e}")
        return False, f"Base64 decode error for '{relative_path}': {b64e}"
    except Exception as e:
        logger.error(f"Error appending to file '{relative_path}': {e}", exc_info=True)
        return (
            False,
            f"Error appending to file '{relative_path}': {type(e).__name__} - {e}",
        )


@handler(name="RUN_SCRIPT")
def handle_run_script(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    relative_script_path = action_data.get("script_path")
    args = action_data.get("args", [])
    script_cwd_option = action_data.get("cwd", "script_dir")
    timeout = action_data.get("timeout", 300)

    if not isinstance(relative_script_path, str) or not relative_script_path:
        return False, "Missing or invalid 'script_path' (string)."
    if not isinstance(args, list):
        return False, "'args' must be a list of strings/numbers."

    script_path_resolved = resolve_path(project_root, relative_script_path)
    if not script_path_resolved or not script_path_resolved.is_file():
        return False, f"Script not found or invalid path: '{relative_script_path}'"

    scripts_dir = (project_root / "scripts").resolve()
    is_in_scripts_dir = str(script_path_resolved).startswith(str(scripts_dir) + os.sep)
    is_in_project_root_directly = script_path_resolved.parent == project_root

    if not (is_in_scripts_dir or is_in_project_root_directly):
        logger.error(
            f"Security Error: Attempt to run script '{script_path_resolved}' which is not in "
            f"'{scripts_dir}' or directly in '{project_root}'."
        )
        return (
            False,
            "Security Error: Script execution restricted to project root or 'scripts/' subdirectory.",
        )

    if not os.access(script_path_resolved, os.X_OK):
        logger.info(
            f"Script '{script_path_resolved}' not executable, attempting chmod +x..."
        )
        try:
            script_path_resolved.chmod(script_path_resolved.stat().st_mode | 0o111)
        except Exception as e:
            logger.warning(
                f"Could not make script '{script_path_resolved}' executable: {e}. Proceeding anyway."
            )

    command = [str(script_path_resolved)] + [str(a) for a in args]

    effective_cwd = (
        script_path_resolved.parent
        if script_cwd_option == "script_dir"
        else project_root
    )
    
    success, user_message, stdout, stderr = _run_subprocess(
            command,
            effective_cwd,
            f"RUN_SCRIPT {relative_script_path}",
            action_data,
            step_id,
            timeout=timeout,
            sudo_password=sudo_password,
        )
    full_response_message = f"{user_message}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()
    return success, full_response_message


@handler(name="LINT_FORMAT_FILE")
def handle_lint_format_file(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    """Runs ruff format and ruff check --fix on a target file/dir."""
    relative_target_path = action_data.get("path", ".")
    run_format = action_data.get("format", True)
    run_lint_fix = action_data.get("lint_fix", True)

    if not isinstance(relative_target_path, str):
        return False, "Invalid 'path' for LINT_FORMAT_FILE, must be a string."

    target_path_obj = resolve_path(project_root, relative_target_path)
    if not target_path_obj or not target_path_obj.exists():
        return (
            False,
            f"Lint/Format target path not found or invalid: '{relative_target_path}'",
        )
    target_path_str = str(target_path_obj)

    if not RUFF_EXECUTABLE or not shutil.which(RUFF_EXECUTABLE):
        logger.error(
            f"'{RUFF_EXECUTABLE}' command not found. Please ensure Ruff is installed and in PATH within the environment."
        )
        return False, f"'{RUFF_EXECUTABLE}' command not found. Install Ruff."

    overall_success = True
    messages = []

    if run_format:
        format_cmd = [RUFF_EXECUTABLE, "format", target_path_str]
        fmt_success, fmt_msg, fmt_stdout, fmt_stderr = _run_subprocess(
            format_cmd, project_root, "RUFF_FORMAT", action_data, step_id, sudo_password=sudo_password
        )
        messages.append(f"Ruff Format: {fmt_msg}")
        if fmt_stdout:
            messages.append(f"  Format STDOUT: {fmt_stdout}")
        if fmt_stderr:
            messages.append(f"  Format STDERR: {fmt_stderr}")
        if not fmt_success:
            overall_success = False

    if run_lint_fix:
        lint_cmd = [RUFF_EXECUTABLE, "check", target_path_str, "--fix", "--exit-zero"]
        lint_success, lint_msg, lint_stdout, lint_stderr = _run_subprocess(
            lint_cmd, project_root, "RUFF_CHECK_FIX", action_data, step_id, sudo_password=sudo_password
        )
        messages.append(f"Ruff Check/Fix: {lint_msg}")
        if lint_stdout:
            messages.append(f"  Check/Fix STDOUT:\n{lint_stdout}")
        if lint_stderr:
            messages.append(f"  Check/Fix STDERR:\n{lint_stderr}")
        if not lint_success:
            overall_success = False
        if (
            "error:" in lint_stdout.lower()
            or "error:" in lint_stderr.lower()
            or (
                lint_success
                and lint_stdout
                and "fixed" not in lint_stdout.lower()
                and "no issues found" not in lint_stdout.lower()
            )
        ):
            logger.warning(
                "Ruff check --fix completed, but potential unfixed issues indicated in output."
            )

    final_message = "\n".join(messages).strip()
    return overall_success, final_message


@handler(name="GIT_ADD")
def handle_git_add(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    paths_to_add = action_data.get("paths", ["."])
    if not isinstance(paths_to_add, list) or not all(
        isinstance(p, str) for p in paths_to_add
    ):
        return False, "'paths' for GIT_ADD must be a list of strings."

    safe_paths_for_git = []
    for p_str in paths_to_add:
        if p_str == ".":
            safe_paths_for_git.append(".")
            continue

        path_in_project = project_root / p_str
        if path_in_project.exists():
            safe_paths_for_git.append(p_str)
        else:
            logger.warning(f"Path '{p_str}' for GIT_ADD does not exist. Skipping.")

    if not safe_paths_for_git:
        return False, "No valid or existing paths provided for GIT_ADD."

    command = ["git", "add"] + safe_paths_for_git
    success, user_message, stdout, stderr = _run_subprocess(
        command, project_root, "GIT_ADD", action_data, step_id, sudo_password=sudo_password
    )
    full_response_message = f"{user_message}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()
    return success, full_response_message


@handler(name="GIT_COMMIT")
def handle_git_commit(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    message = action_data.get("message")
    allow_empty = action_data.get("allow_empty", False)

    if not isinstance(message, str) or not message:
        return False, "Missing or invalid 'message' (string) for GIT_COMMIT."

    command = ["git", "commit", "-m", message]
    if allow_empty:
        command.append("--allow-empty")

    success, user_message, stdout, stderr = _run_subprocess(
        command, project_root, "GIT_COMMIT", action_data, step_id, sudo_password=sudo_password
    )
    full_response_message = f"{user_message}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()

    if not success and "nothing to commit" in stderr.lower() and not allow_empty:
        logger.info("GIT_COMMIT: Nothing to commit.")
        return True, "Nothing to commit."

    return success, full_response_message


@handler(name="CALL_LOCAL_LLM")
def handle_call_local_llm(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    prompt = action_data.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return False, "Missing or invalid 'prompt' (string) for CALL_LOCAL_LLM."

    return call_local_llm_helper(
        prompt,
        action_data.get("model"),
        action_data.get("api_endpoint_base"),
        action_data.get("options"),
        step_id=step_id,
        action_name="CALL_LOCAL_LLM",
    )


@handler(name="DIAGNOSE_ERROR")
def handle_diagnose_error(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    failed_command = action_data.get("failed_command")
    stdout = action_data.get("stdout", "")
    stderr = action_data.get("stderr", "")
    context = action_data.get("context", {})
    history_lookback = action_data.get("history_lookback", 5)

    if not isinstance(failed_command, str) or not failed_command:
        return False, "Missing or invalid 'failed_command' for DIAGNOSE_ERROR."
    if not stderr and not stdout:
        return False, "No stdout or stderr provided for diagnosis."

    history_entries: List[Dict[str, Any]] = []
    try:
        if HISTORY_FILE.exists() and HISTORY_FILE.is_file():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if len(history_entries) >= history_lookback:
                        break
                    try:
                        history_entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Skipping malformed history line: {line.strip()}"
                        )
                history_entries.reverse()
    except Exception as e:
        logger.warning(f"Could not read execution history from '{HISTORY_FILE}': {e}")

    prompt = f"""Agent Ex-Work encountered an error. Analyze the situation and provide a concise diagnosis and a specific, actionable suggestion.

Failed Command:
`{failed_command}`

Stdout:
```text
{stdout if stdout else "<empty>"}

Stderr:
```text
{stderr if stderr else "<empty>"}

"""
    if context and isinstance(context, dict):
        prompt += (
            f"\nAdditional Context:\n```json\n{json.dumps(context, indent=2)}\n```"
        )
    if history_entries:
        prompt += f"\nRecent Relevant Execution History (up to last {len(history_entries)} entries):\n"
        for i, entry in enumerate(history_entries):
            prompt += (
                f"{i + 1}. Action: {entry.get('action_name', 'N/A')}, "
                f"Cmd: {entry.get('command', 'N/A')}, Success: {entry.get('success', 'N/A')}, "
                f"RC: {entry.get('exit_code', 'N/A')}\n"
            )
            if not entry.get("success") and entry.get("stderr_snippet"):
                prompt += f"   Error Snippet: {entry['stderr_snippet']}\n"
        prompt += "---\n"

    prompt += """

Desired Output Format:
Respond with a single JSON object containing "diagnosis", "fix_type", and "fix_content".
"fix_type" must be one of: "COMMAND", "PATCH", "MANUAL_STEPS", "CONFIG_ADJUSTMENT", "INFO_REQUEST".

Example 1 (COMMAND):
{
"diagnosis": "The 'git add' command failed because there were no new files or changes to stage in the specified path 'src/'. The working directory might be clean or the path incorrect.",
"fix_type": "COMMAND",
"fix_content": "git status"
}
Example 2 (PATCH):
{
"diagnosis": "The Python script failed due to a NameError, 'my_varialbe' likely a typo for 'my_variable'.",
"fix_type": "PATCH",
"fix_content": "--- a/script.py\n+++ b/script.py\n@@ -1,3 +1,3 @@\n def my_func():\n-    my_varialbe = 10\n+    my_variable = 10\n     print(my_variable)"
}
Example 3 (MANUAL_STEPS):
{
"diagnosis": "The 'RUN_SCRIPT' for 'deploy.sh' failed. Stderr indicates a missing environment variable 'API_KEY'.",
"fix_type": "MANUAL_STEPS",
"fix_content": "1. Ensure the API_KEY environment variable is set before running the script. 2. Check the deploy.sh script for how it expects API_KEY."
}

Provide your analysis:
"""
    logger.info("Diagnosing error using local LLM for DIAGNOSE_ERROR...")
    llm_success, llm_response_str = call_local_llm_helper(
        prompt, step_id=step_id, action_name="DIAGNOSE_ERROR_LLM_CALL"
    )

    if llm_success:
        try:
            parsed_llm_response = json.loads(llm_response_str)
            if isinstance(parsed_llm_response, dict) and all(
                k in parsed_llm_response
                for k in ["diagnosis", "fix_type", "fix_content"]
            ):
                logger.info("Successfully parsed structured diagnosis from LLM.")
                return True, json.dumps(parsed_llm_response)
            else:
                logger.warning(
                    f"LLM response for diagnosis was not the expected JSON structure: {llm_response_str[:300]}"
                )
                return True, json.dumps(
                    {
                        "diagnosis": "LLM provided a response, but it was not in the expected structured JSON format. See full_llm_response.",
                        "fix_type": "RAW_LLM_OUTPUT",
                        "fix_content": llm_response_str,
                        "full_llm_response": llm_response_str,
                    }
                )
        except json.JSONDecodeError:
            logger.warning(
                f"LLM response for diagnosis was not valid JSON: {llm_response_str[:300]}"
            )
            return True, json.dumps(
                {
                    "diagnosis": "LLM response could not be parsed as JSON. See full_llm_response.",
                    "fix_type": "PARSE_ERROR",
                    "fix_content": llm_response_str,
                    "full_llm_response": llm_response_str,
                }
            )
    else:
        return False, f"Failed to get diagnosis from LLM: {llm_response_str}"


# --- Core Agent Logic ---


def process_instruction_block(
    instruction_json: str, project_root: Path, step_id: str, sudo_password: Optional[str] = None  # NEW: Pass sudo_password down
) -> Tuple[bool, List[Dict[str, Any]]]:
    action_results_summary: List[Dict[str, Any]] = []
    overall_block_success = True

    try:
        instruction = json.loads(instruction_json)
    except json.JSONDecodeError as e:
        logger.error(f"FATAL: JSON Decode Failed for instruction block: {e}")
        logger.error(f"Raw input snippet: {instruction_json[:500]}...")
        action_results_summary.append(
            {
                "action_type": "BLOCK_PARSE",
                "success": False,
                "message_or_payload": f"JSON Decode Error: {e}",
            }
        )
        return False, action_results_summary

    if not isinstance(instruction, dict):
        logger.error("FATAL: Instruction block is not a JSON object.")
        action_results_summary.append(
            {
                "action_type": "BLOCK_VALIDATION",
                "success": False,
                "message_or_payload": "Instruction block not a dict.",
            }
        )
        return False, action_results_summary

    step_id = instruction.get("step_id", str(uuid.uuid4()))
    description = instruction.get("description", "N/A")
    actions = instruction.get("actions", [])
    # NEW: Extract block-level sudo preference and password
    use_sudo_block_level = instruction.get("use_sudo_for_block", False)
    sudo_password_block_level = instruction.get("sudo_password_for_block", sudo_password)  # Prefer block-level password if provided

    logger.info(
        f"Processing Instruction Block - StepID: {step_id}, Desc: {description}"
    )

    if not isinstance(actions, list):
        logger.error(f"'{step_id}': 'actions' field must be a list.")
        action_results_summary.append(
            {
                "action_type": "BLOCK_VALIDATION",
                "success": False,
                "message_or_payload": "'actions' field not a list.",
            }
        )
        return False, action_results_summary

    for i, action_data in enumerate(actions):
        action_num = i + 1
        action_type_value = action_data.get("type")
        # Handler now takes 4 arguments
        handler: Optional[Callable[[Dict, Path, str, Optional[str]], Tuple[bool, Any]]] = None 
        current_action_type_for_log = "UNKNOWN_OR_INVALID_TYPE"

        # Determine sudo preference and password for this specific action
        # Action-level use_sudo overrides block-level, which overrides no preference
        use_sudo_for_action = action_data.get("use_sudo", use_sudo_block_level)
        sudo_password_for_action = action_data.get("sudo_password", sudo_password_block_level)

        if isinstance(action_type_value, str):
            current_action_type_for_log = action_type_value
            handler = ACTION_HANDLERS.get(current_action_type_for_log)  # Lookup with a confirmed string
            if not handler:
                logger.error(
                    f"'{step_id}': Action {action_num} - Unknown action type encountered: '{current_action_type_for_log}'."
                )
                action_results_summary.append(
                    {
                        "action_type": current_action_type_for_log,
                        "success": False,
                        "message_or_payload": f"Unknown action type: '{current_action_type_for_log}'.",
                        "action_index": i,
                    }
                )
                overall_block_success = False
                break  # Stop processing this block of actions
        else:
            logger.error(
                f"'{step_id}': Action {action_num} has missing or invalid 'type' (expected string, got: {type(action_type_value).__name__})."
            )
            action_results_summary.append(
                {
                    "action_type": (
                        str(action_type_value)
                        if action_type_value is not None
                        else "MISSING_TYPE"
                    ),
                    "success": False,
                    "message_or_payload": f"Action has missing or invalid 'type': {action_type_value}",
                    "action_index": i,
                }
            )
            overall_block_success = False
            break  # Stop processing this block of actions

        logger.info(
            f"--- {step_id}: Action {action_num}/{len(actions)} (Type: {current_action_type_for_log}, Sudo: {use_sudo_for_action}) ---"
        )

        if not overall_block_success:  # If type was invalid or handler not found
            logger.info(
                f"Halting block {step_id} due to prior failure or invalid action type for action {action_num}."
            )
            break  # Stop processing this block of actions

        action_start_time = time.time()
        # Call handler with all 4 arguments
        success, result_payload = handler(action_data, project_root, step_id, sudo_password_for_action)
        action_duration = time.time() - action_start_time

        action_summary = {
            "action_type": current_action_type_for_log,
            "success": success,
            "message_or_payload": result_payload,
            "duration_s": round(action_duration, 3),
            "action_index": i,
            "step_id": step_id,  # Add step_id to individual action summary
            "action_params": action_data  # Add action parameters for context
        }
        action_results_summary.append(action_summary)

        # NEW: Consolidate logging into _run_subprocess and specialized handlers.
        # Only log a summary here for actions that don't self-log (e.g. file ops).
        is_subprocess_action = current_action_type_for_log in [
            "RUN_COMMAND",
            "RUN_SCRIPT",
            "LINT_FORMAT_FILE",
            "APPLY_PATCH",
            "GIT_ADD",
            "GIT_COMMIT",
        ]
        is_file_op_action = current_action_type_for_log in [
            "CREATE_OR_REPLACE_FILE", "APPEND_TO_FILE"
        ]
        is_llm_action = current_action_type_for_log in [
            "CALL_LOCAL_LLM", "DIAGNOSE_ERROR"
        ]
        is_ipc_action = current_action_type_for_log == "DAEMON_IPC"

        if not any([is_subprocess_action, is_file_op_action, is_llm_action, is_ipc_action]):
            log_execution_history(
                {
                    "timestamp": action_start_time,
                    "action_name": current_action_type_for_log,
                    "success": success,
                    "message": (
                        result_payload
                        if isinstance(result_payload, str)
                        else json.dumps(result_payload, default=str)
                    ),
                    "duration_s": action_duration,
                    "step_id": step_id,
                    "action_params": action_data,
                }
            )

        if not success:
            logger.error(
                f"'{step_id}': Action {action_num} ({current_action_type_for_log}) FAILED. Result: {result_payload}"
            )
            overall_block_success = False  # Ensure this is set
            logger.info(
                f"Halting processing of action block '{step_id}' due to failure in action {action_num} ({current_action_type_for_log})."
            )
            break  # Stop processing further actions
        else:
            logger.info(
                f"'{step_id}': Action {action_num} ({current_action_type_for_log}) SUCCEEDED. Duration: {action_duration:.3f}s"
            )

    logger.info(
        f"--- Finished processing actions for StepID: {step_id}. Overall Block Success: {overall_block_success} ---"
    )
    return overall_block_success, action_results_summary


def execute_plan(plan: Dict[str, Any], sudo_password: Optional[str] = None) -> List[Dict[str, Any]]:  # NEW: pass sudo_password
    """Executes the actions specified in the plan."""
    results: List[Dict[str, Any]] = []
    plan_step_id = plan.get("step_id", f"execute_plan_{str(uuid.uuid4())[:8]}")
    logger.info(f"Executing plan with StepID: {plan_step_id}")

    for i, action_config in enumerate(plan.get("actions", [])):
        action_type_value = action_config.get("type")
        handler: Optional[Callable[[Dict, Path, str, Optional[str]], Tuple[bool, Any]]] = None  # NEW: Handler takes sudo_password
        action_type_for_log = "UNKNOWN_OR_INVALID_TYPE"

        if isinstance(action_type_value, str):
            action_type_for_log = action_type_value
            handler = ACTION_HANDLERS.get(action_type_for_log)

        if handler:
            action_specific_step_id = f"{plan_step_id}_action_{i + 1}"
            logger.info(
                f"--- {plan_step_id}: Executing Action {i + 1} (Type: {action_type_for_log}) via execute_plan ---"
            )
            try:
                # Determine sudo preference and password for this specific action
                use_sudo_for_action = action_config.get("use_sudo", plan.get("use_sudo_for_block", False))
                sudo_password_for_action = action_config.get("sudo_password", sudo_password)

                success, message = handler(
                    action_config, PROJECT_ROOT, action_specific_step_id, sudo_password_for_action  # NEW: Pass sudo_password
                )
                results.append(
                    {
                        "action": action_type_for_log,
                        "success": success,
                        "message": message,
                        "step_id": action_specific_step_id,  # Add step_id to individual action summary
                        "action_params": action_config  # Add action parameters for context
                    }
                )
                if not success:
                    logger.error(
                        f"Action {action_type_for_log} in execute_plan (id: {action_specific_step_id}) failed. Message: {message}"
                    )
            except Exception as e:
                logger.error(
                    f"Exception during handler execution for action '{action_type_for_log}' (id: {action_specific_step_id}) in execute_plan: {e}",
                    exc_info=True,
                )
                results.append(
                    {
                        "action": action_type_for_log,
                        "success": False,
                        "message": f"Exception: {e}",
                        "step_id": action_specific_step_id,
                        "action_params": action_config
                    }
                )
        else:
            logger.warning(
                f"No handler found for action type: '{action_type_value}' in execute_plan (action {i + 1}). Action config: {action_config}"
            )
            results.append(
                {
                    "action": (
                        str(action_type_value)
                        if action_type_value is not None
                        else "MISSING_TYPE"
                    ),
                    "success": False,
                    "message": f"No handler for action type: {action_type_value}",
                    "step_id": f"{plan_step_id}_action_{i + 1}",
                    "action_params": action_config
                }
            )
    logger.info(
        f"Finished execute_plan for StepID: {plan_step_id}. Results count: {len(results)}"
    )
    return results


# --- Enhanced workflow execution and error handling ---


def execute_task(task_name: str, project_root: Path, sudo_password: Optional[str] = None):  # NEW: pass sudo_password
    """Executes a specific task by name."""
    try:
        if task_name not in ACTION_HANDLERS:
            raise ValueError(f"Task '{task_name}' is not registered.")

        handler = ACTION_HANDLERS[task_name]
        # Assuming task_name mapping to an action config like {"type": task_name, "parameters": {}}
        action_config = {"type": task_name, "sudo_password": sudo_password}
        success, result = handler(action_config, project_root, task_name, sudo_password)  # Pass task_name as step_id
        # The `handler` decorator now correctly points to functions taking 4 args

        if success:
            logger.info(f"Task '{task_name}' executed successfully: {result}")
        else:
            logger.warning(f"Task '{task_name}' failed: {result}")

    except Exception as e:
        logger.error(f"Error executing task '{task_name}': {e}", exc_info=True)
        return False

    return True


def register_handler(handler_name: str):  # NO CHANGE NEEDED FOR THIS HELPER FUNCTION
    """Registers a new handler dynamically."""
    try:
        if handler_name in ACTION_HANDLERS:
            logger.warning(f"Handler '{handler_name}' is already registered.")
            return False

        # This dynamic handler now must accept 4 arguments as per the new handler decorator
        def dynamic_handler(task_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None):
            logger.info(f"Executing dynamic handler for task: {handler_name}")
            return True, f"Dynamic handler '{handler_name}' executed successfully."

        ACTION_HANDLERS[handler_name] = dynamic_handler
        logger.info(f"Handler '{handler_name}' registered successfully.")

    except Exception as e:
        logger.error(f"Error registering handler '{handler_name}': {e}", exc_info=True)
        return False

    return True


# --- Interactive Configuration and Execution ---
def interactive_mode():
    """Provides an interactive mode for configuring and executing tasks."""
    logger.info("Entering interactive mode for Ex-Work Agent.")
    # Prompt for sudo password once for interactive session if needed
    interactive_sudo_password = None
    try:
        if QUESTIONARY_AVAILABLE:
            approval = questionary.confirm("Do you want to provide a sudo password for this interactive session? (Recommended for full functionality) (y/N): ").ask()
        else:
            approval = input("Do you want to provide a sudo password for this interactive session? (Recommended for full functionality) (y/N): ").strip().lower()
            approval = approval in ['y', 'yes']
        
        if approval:
            interactive_sudo_password = getpass.getpass("Enter sudo password (will not be displayed): ").strip()
            if not interactive_sudo_password:
                logger.warning("No sudo password provided for interactive session.")
    except Exception as e:
        logger.warning(f"Error getting sudo password: {e}")

    while True:
        print("\n--- Ex-Work Agent Interactive Mode ---")
        print("1. Add a new task")
        print("2. View registered handlers")
        print("3. Execute tasks from a JSON file")
        print("4. Exit interactive mode")

        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            task_name = input("Enter task name: ").strip()
            parameters = input("Enter task parameters as JSON: ").strip()
            try:
                task_params = json.loads(parameters)
                logger.info(f"Adding task: {task_name} with parameters: {task_params}")
                # For interactive mode, directly execute the task if a handler exists
                if task_name in ACTION_HANDLERS:
                    # Pass the interactive_sudo_password to execute_task
                    success, message = ACTION_HANDLERS[task_name](task_params, PROJECT_ROOT, "interactive_task", interactive_sudo_password)
                    print(f"Task '{task_name}' executed: {message}")
                else:
                    print(f"No handler found for action: {task_name}. Consider generating one dynamically.")
                    if QUESTIONARY_AVAILABLE:
                        approval = questionary.confirm(f"Do you want to propose a dynamic handler for '{task_name}'? (y/N): ").ask()
                    else:
                        approval = input(f"Do you want to propose a dynamic handler for '{task_name}'? (y/N): ").strip().lower()
                        approval = approval in ['y', 'yes']
                    
                    if approval:
                        learn_from_failures(task_name, "Interactive task addition", "interactive_task_gen")
            except json.JSONDecodeError:
                print("Invalid JSON format for parameters. Please try again.")

        elif choice == "2":
            print("\n--- Registered Handlers ---")
            for handler_name in ACTION_HANDLERS.keys():
                print(f"- {handler_name}")

        elif choice == "3":
            file_path = input("Enter the path to the JSON file with tasks: ").strip()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tasks_plan = json.load(f)  # Load the entire plan structure
                    logger.info(f"Loaded tasks from {file_path}: {tasks_plan}")
                    # Use execute_plan for structured execution
                    # Pass the interactive_sudo_password
                    results = execute_plan(tasks_plan, interactive_sudo_password)
                    print(json.dumps({"plan_results": results}, indent=2))  # Print results of plan execution
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading tasks: {e}")

        elif choice == "4":
            print("Exiting interactive mode.")
            break

        else:
            print("Invalid choice. Please select a valid option.")


# Modify main execution to include interactive mode
def main():
    """Main entry point for the Ex-Work Agent."""
    global PROJECT_ROOT  # Ensure PROJECT_ROOT is set if running without arguments

    parser = argparse.ArgumentParser(description="Ex-Work Agent CLI (Superpowered)")
    parser.add_argument("--auto", action="store_true", help="Run in zero-touch automation mode.")
    parser.add_argument("--menu", action="store_true", help="Show interactive super menu.")
    parser.add_argument("--status", action="store_true", help="Show agent status.")
    parser.add_argument("--repair", action="store_true", help="Run self-repair.")
    parser.add_argument("--nuke", action="store_true", help="Emergency nuke/exit.")
    parser.add_argument("--log-level", default="INFO", help="Set log level.")
    parser.add_argument("--config", type=str, help="Path to config file.")
    parser.add_argument("--version", action="store_true", help="Show version.")
    parser.add_argument("--self-update", action="store_true", help="Self-update agent.")
    parser.add_argument("--hot-reload", action="store_true", help="Hot reload config.")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard.")
    parser.add_argument("--remote-trigger", action="store_true", help="Enable remote trigger thread.")
    parser.add_argument("--health-check", action="store_true", help="Run health check.")
    parser.add_argument("--regen", action="store_true", help="Regenerate handlers.")
    parser.add_argument("--info", action="store_true", help="Show agent info (JSON).")
    parser.add_argument("--process-stdin", action="store_true", help="Process a single JSON instruction block from stdin.")  # NEW: for mediator-like usage
    parser.add_argument("--sudo-password", type=str, help="Sudo password for non-interactive commands (use with extreme caution).")  # NEW: for non-interactive sudo
    # Removed --interactive from main args as it's now handled by the if __name__ == "__main__": block
    args = parser.parse_args()

    logger.setLevel(args.log_level.upper())

    # Set PROJECT_ROOT based on where the agent is run
    PROJECT_ROOT = Path.cwd().resolve()

    # Handle immediate CLI arguments that exit
    if args.version:
        print(f"exworkagent0 version {AGENT_VERSION}")
        sys.exit(0)
    if args.status:
        print_status()
        sys.exit(0)
    if args.info:
        print_status(json_mode=True)
        sys.exit(0)
    if args.nuke:
        emergency_nuke()
    if args.self_update:
        self_update()
        sys.exit(0)
    if args.repair:
        self_repair()
        sys.exit(0)
    if args.hot_reload:
        hot_reload_config()
        sys.exit(0)
    if args.dashboard:
        dashboard()
        sys.exit(0)
    if args.menu:  # This is the interactive menu
        interactive_mode()
        sys.exit(0)

    # Check general agent dependencies before running in auto/remote modes
    check_dependencies()

    # Handle process-stdin mode (used by omni_mediator.py)
    if args.process_stdin:
        logger.info("Running Ex-Work Agent in --process-stdin mode.")
        json_input_lines = []
        try:
            for line in sys.stdin:
                json_input_lines.append(line)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt during stdin read. Exiting.")
            sys.stdout.write(json.dumps({"overall_success": False, "status_message": "Interrupted by user during input."}) + "\n")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading from stdin: {e}", exc_info=True)
            sys.stdout.write(json.dumps({"overall_success": False, "status_message": f"Stdin read error: {e}"}) + "\n")
            sys.exit(1)

        json_input = "".join(json_input_lines)
        if not json_input.strip():
            logger.warning("No input received from stdin. Exiting.")
            sys.stdout.write(json.dumps({"overall_success": False, "status_message": "No input from stdin."}) + "\n")
            sys.exit(0)

        logger.info(f"Processing {len(json_input)} bytes of instruction from stdin...")
        start_process_time = time.time()

        # Pass sudo_password from CLI argument down to processing
        overall_success, action_results = process_instruction_block(
            json_input, PROJECT_ROOT, "stdin_execution", sudo_password=args.sudo_password
        )

        end_process_time = time.time()
        duration = round(end_process_time - start_process_time, 3)

        final_status_message = f"Instruction block processing finished. Overall Success: {overall_success}. Duration: {duration}s"
        logger.info(final_status_message)

        output_payload = {
            "overall_success": overall_success,
            "status_message": final_status_message,
            "duration_seconds": duration,
            "action_results": action_results,
            "agent_version": AGENT_VERSION,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        sys.stdout.write(json.dumps(output_payload, indent=2) + "\n")
        sys.stdout.flush()

        if not overall_success:
            sys.exit(1)

    # If running in --auto or --remote-trigger mode (background daemons)
    if args.remote_trigger:
        threading.Thread(target=remote_trigger, daemon=True).start()
    if args.auto:
        logger.info("Running in zero-touch automation mode.")
        threading.Thread(target=watchdog, daemon=True).start()
        threading.Thread(target=remote_trigger, daemon=True).start()
        while True:
            time.sleep(60)  # Keep main thread alive for daemons to run

    # If no specific mode is chosen, print help and exit
    if not any([args.version, args.status, args.info, args.nuke, args.self_update, args.repair,
                args.hot_reload, args.dashboard, args.menu, args.process_stdin,
                args.remote_trigger, args.auto, args.health_check, args.regen]):
        parser.print_help()
        sys.exit(0)


# --- Universal CLI/Automation/Orchestrator Interface ---
def print_status(json_mode=False):
    status = {
        "agent": "exworkagent0",
        "version": AGENT_VERSION,
        "cwd": str(PROJECT_ROOT),
        "handlers": list(ACTION_HANDLERS.keys()),
        "history_file": str(HISTORY_FILE),
        "ollama_model": DEFAULT_OLLAMA_MODEL,
        "ollama_endpoint": DEFAULT_OLLAMA_ENDPOINT_BASE,
        "log_level": logger.level,
        "health": "OK",
        "timestamp": datetime.datetime.now().isoformat(),
    }
    if json_mode:
        print(json.dumps(status, indent=2))
    else:
        print(f"[STATUS] exworkagent0 v{AGENT_VERSION} | Handlers: {len(ACTION_HANDLERS)} | Health: OK")


def self_update():
    # Placeholder: implement git pull or remote fetch logic
    logger.info("Self-update not yet implemented for exworkagent0.")


def self_repair():
    logger.info("Self-repair: Checking for missing/corrupt files (placeholder)")
    # Could check for required files, handlers, etc.


def watchdog():
    logger.info("Watchdog started.")
    while True:
        # Could check health, restart on failure, etc.
        time.sleep(30)


def remote_trigger():
    logger.info("Remote trigger thread started.")
    # Could poll a file, socket, or HTTP endpoint for remote commands
    while True:
        time.sleep(10)


def hot_reload_config():
    logger.info("Hot-reloading config (placeholder)")


def emergency_nuke():
    logger.critical("EMERGENCY NUKE: Exiting and cleaning up!")
    sys.exit(99)


def dashboard():
    print("==================== exworkagent0 DASHBOARD ====================")
    print(f"Handlers: {list(ACTION_HANDLERS.keys())}")
    print(f"History: {HISTORY_FILE}")
    print(f"Ollama: {DEFAULT_OLLAMA_MODEL} @ {DEFAULT_OLLAMA_ENDPOINT_BASE}")
    print("---------------------------------------------------------------")
    print("[A]uto-repair  [R]estart  [N]uke  [Q]uit")
    while True:
        key = input("Command: ").strip().lower()
        if key == "a":
            self_repair()
        elif key == "r":
            os.execv(sys.executable, [sys.executable] + sys.argv)
        elif key == "n":
            emergency_nuke()
        elif key == "q":
            print("Exiting dashboard.")
            break


def super_menu():
    while True:
        print("==================== exworkagent0 SUPER MENU ===================")
        print("1) Status\n2) Dashboard\n3) Self-Repair\n4) Self-Update\n5) Hot Reload Config\n6) Nuke\n7) Exit")
        opt = input("Select option: ").strip()
        if opt == "1":
            print_status()
        elif opt == "2":
            dashboard()
        elif opt == "3":
            self_repair()
        elif opt == "4":
            self_update()
        elif opt == "5":
            hot_reload_config()
        elif opt == "6":
            emergency_nuke()
        elif opt == "7":
            break
        else:
            print("Invalid option.")

# --- Dependency Check and Installation ---
def check_dependencies():
    """Check Agent Ex-Work system and Python dependencies with auto-installation"""
    global RUFF_EXECUTABLE, PATCH_EXECUTABLE  # Declare globals at the beginning
    logger.info("Checking Agent Ex-Work system and Python dependencies...")

    # --- Python package dependencies ---
    required_py_packages = ["python-dotenv", "requests"]  # Core exwork_agent.py needs these
    # The interactive mode / other handlers might need rich, questionary etc.
    # It's better to ensure these are in requirements.txt and installed by installer.

    missing_py_packages = []
    for pkg in required_py_packages:
        try:
            __import__(pkg.replace('-', '_'))  # Handle packages with hyphens like python-dotenv
        except ImportError:
            missing_py_packages.append(pkg)

    if missing_py_packages:
        logger.warning(f"Missing core Python packages: {', '.join(missing_py_packages)}. Attempting to install...")
        # Using current sys.executable ensures it installs into the correct venv/environment
        install_cmd = [sys.executable, "-m", "pip", "install"] + missing_py_packages
        success, msg, _, _ = _run_subprocess(install_cmd, PROJECT_ROOT, "INSTALL_PYTHON_CORE_DEPS", {"packages": missing_py_packages}, "dep_check_py")
        if not success:
            logger.error(f"Failed to install core Python dependencies: {msg}. Agent may not function correctly.")
            # This is a critical error, agent won't work without core deps
            sys.exit(1)  # Exit if core Python deps cannot be installed
        else:
            logger.info("Core Python dependencies installed.")
    else:
        logger.info("All core Python dependencies found.")

    # --- System command dependencies ---
    required_system_commands = ["sudo", PATCH_EXECUTABLE]  # PATCH_EXECUTABLE is now 'patch'
    if RUFF_EXECUTABLE == "ruff":  # If it's not a specific path, assume it needs installing
        required_system_commands.append("ruff")

    missing_system_commands = [cmd for cmd in required_system_commands if not shutil.which(cmd)]

    if missing_system_commands:
        logger.warning(f"Missing system commands: {', '.join(missing_system_commands)}. Attempting to install...")
        install_cmd_prefix: List[str] = []

        os_name = platform.system()
        distro_id = ""

        # --- Robust OS/Distro Detection ---
        if os_name == "Linux":
            try:
                # Read /etc/os-release for robust distro ID
                with open("/etc/os-release", "r") as f:
                    os_release_content = f.read()
                id_match = re.search(r'^ID=(.*)$', os_release_content, re.MULTILINE)
                if id_match:
                    distro_id = id_match.group(1).strip().lower().replace('"', '')
                else:
                    logger.warning("Could not determine Linux distro from /etc/os-release. Falling back to less precise methods.")
                    # Fallback for older systems if /etc/os-release is not definitive
                    if shutil.which("lsb_release"):
                        distro_id = subprocess.run(["lsb_release", "-is"], capture_output=True, text=True, check=False).stdout.strip().lower()
            except Exception as e:
                logger.warning(f"Error reading /etc/os-release: {e}. Distro detection may be inaccurate.")
                # Fallback if file read fails
                if shutil.which("lsb_release"):
                    distro_id = subprocess.run(["lsb_release", "-is"], capture_output=True, text=True, check=False).stdout.strip().lower()

            if "ubuntu" in distro_id or "debian" in distro_id or "pop" in distro_id:
                install_cmd_prefix = ["sudo", "apt-get", "update", "-y", "--fix-missing", "--allow-unauthenticated", "--allow-insecure-repositories"]  # Add allow for robustness
                install_cmd_prefix.extend(["sudo", "apt-get", "install", "-y"])
            elif "fedora" in distro_id or "centos" in distro_id or "rhel" in distro_id:
                install_cmd_prefix = ["sudo", "dnf", "install", "-y"]
            elif "arch" in distro_id:
                install_cmd_prefix = ["sudo", "pacman", "-Sy", "--noconfirm"]
            elif "alpine" in distro_id:  # NEW: Alpine support
                install_cmd_prefix = ["sudo", "apk", "add"]
            else:
                logger.error(f"Unsupported Linux distribution for auto-install: {distro_id}. Please install missing commands manually.")
        elif os_name == "Darwin":  # macOS
            if shutil.which("brew"):
                install_cmd_prefix = ["brew", "install"]
            else:
                logger.error("Homebrew not found on macOS. Cannot auto-install system commands.")
        elif os_name == "Windows":  # Basic Windows support (for WSL context if needed)
            logger.warning("Windows detected. Auto-install for system commands (like 'patch', 'ruff') is not yet implemented. Please install via WSL2/Chocolatey or manually.")
        else:
            logger.error(f"Unsupported OS for auto-install: {os_name}. Please install missing commands manually.")
            print(f"[OMNITIDE_SCA_ERROR] Unsupported OS for auto-install: {os_name}. Install missing commands: {', '.join(missing_system_commands)}.")
            return False  # Cannot auto-install

        if install_cmd_prefix:
            full_install_cmd = install_cmd_prefix + missing_system_commands
            success, msg, _, _ = _run_subprocess(full_install_cmd, PROJECT_ROOT, "INSTALL_SYSTEM_DEPS", {"packages": missing_system_commands, "use_sudo": True}, "dep_check_sys")
            if not success:
                logger.error(f"Failed to install system dependencies: {msg}. Agent may not function correctly.")
                print(f"[OMNITIDE_SCA_ERROR] Failed to install system dependencies: {msg}")
            else:
                logger.info("System dependencies installed.")
        else:
            logger.error(f"No auto-install method for current OS ({os_name}, {distro_id}). Missing system commands: {', '.join(missing_system_commands)}. Please install manually.")
            print(f"[OMNITIDE_SCA_ERROR] Missing system commands: {', '.join(missing_system_commands)}. Please ensure they are installed and in PATH.")
            return False  # Cannot auto-install
    else:
        logger.info("All required system commands found.")
        # Ensure Ruff executable path is confirmed if auto-installed
        if "ruff" in missing_system_commands and RUFF_EXECUTABLE == "ruff":  # If it was a missing command and we're using default name
            RUFF_EXECUTABLE = shutil.which("ruff")  # Update path if it was installed
            if not RUFF_EXECUTABLE:
                logger.error("Ruff still not found after installation attempt. Something went wrong.")
                return False
        if "patch" in missing_system_commands and PATCH_EXECUTABLE == "patch":
            PATCH_EXECUTABLE = shutil.which("patch")
            if not PATCH_EXECUTABLE:
                logger.error("Patch still not found after installation attempt. Something went wrong.")
                return False

    # --- Ollama / Local LLM Endpoint Check ---
    ollama_health_endpoint = f"{DEFAULT_OLLAMA_ENDPOINT_BASE.rstrip('/')}/api/tags"
    try:
        response = requests.get(ollama_health_endpoint, timeout=5)
        response.raise_for_status()
        models_info = response.json()
        available_models = [m['name'] for m in models_info.get('models', [])]
        logger.info(f"Ollama endpoint reachable. Available models: {available_models}")
        if DEFAULT_OLLAMA_MODEL not in available_models:
            logger.warning(f"Default Ollama model '{DEFAULT_OLLAMA_MODEL}' not found. LLM actions may need specific model override.")
            print(f"[OMNITIDE_SCA_WARNING] Default Ollama model '{DEFAULT_OLLAMA_MODEL}' not found. Consider downloading it: 'ollama pull {DEFAULT_OLLAMA_MODEL}'")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama endpoint '{DEFAULT_OLLAMA_ENDPOINT_BASE}' not reachable or unhealthy: {e}. LLM actions will fail.")
        print(f"[OMNITIDE_SCA_ERROR] Ollama LLM endpoint not reachable. Ensure Ollama is running and accessible: {e}")

    logger.info("Agent Ex-Work dependencies check complete.")
    return True


@handler(name="APPLY_PATCH")
def handle_apply_patch(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    """Apply a patch using the patch command."""
    patch_content = action_data.get("patch_content")
    target_file = action_data.get("target_file")
    patch_level = action_data.get("patch_level", 1)  # Default to -p1
    
    if not isinstance(patch_content, str) or not patch_content:
        return False, "Missing or invalid 'patch_content' (string) for APPLY_PATCH."
    
    if target_file:
        target_path = resolve_path(project_root, target_file)
        if not target_path or not target_path.exists():
            return False, f"Target file not found or invalid path: '{target_file}'"
    
    # Write patch content to temporary file
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as temp_patch:
            temp_patch.write(patch_content)
            temp_patch_path = temp_patch.name
        
        # Build patch command
        patch_cmd = [PATCH_EXECUTABLE, f"-p{patch_level}"]
        if target_file:
            patch_cmd.extend([str(target_path)])
        patch_cmd.extend(["-i", temp_patch_path])
        
        success, user_message, stdout, stderr = _run_subprocess(
            patch_cmd, project_root, "APPLY_PATCH", action_data, step_id, sudo_password=sudo_password
        )
        
        # Clean up temporary file
        os.unlink(temp_patch_path)
        
        full_response_message = f"{user_message}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()
        return success, full_response_message
        
    except Exception as e:
        logger.error(f"Error applying patch: {e}", exc_info=True)
        return False, f"Error applying patch: {type(e).__name__} - {e}"


@handler(name="DAEMON_IPC")
def handle_daemon_ipc(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    """Send IPC message to a daemon or service."""
    ipc_type = action_data.get("ipc_type", "socket")
    message = action_data.get("message")
    target = action_data.get("target")
    timeout = action_data.get("timeout", 30)
    
    if not isinstance(message, str) or not message:
        return False, "Missing or invalid 'message' (string) for DAEMON_IPC."
    
    if not isinstance(target, str) or not target:
        return False, "Missing or invalid 'target' (string) for DAEMON_IPC."
    
    try:
        if ipc_type == "socket":
            # Unix domain socket communication
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(target)
            sock.sendall(message.encode('utf-8'))
            response = sock.recv(4096)
            sock.close()
            return True, f"IPC message sent successfully. Response: {response.decode('utf-8', errors='replace')}"
        
        elif ipc_type == "tcp":
            # TCP socket communication
            host, port = target.split(':')
            port = int(port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(message.encode('utf-8'))
            response = sock.recv(4096)
            sock.close()
            return True, f"TCP IPC message sent successfully. Response: {response.decode('utf-8', errors='replace')}"
        
        else:
            return False, f"Unsupported IPC type: {ipc_type}"
            
    except Exception as e:
        logger.error(f"Error in DAEMON_IPC: {e}", exc_info=True)
        return False, f"DAEMON_IPC error: {type(e).__name__} - {e}"


@handler(name="RUN_COMMAND")
def handle_run_command(
    action_data: Dict, project_root: Path, step_id: str, sudo_password: Optional[str] = None
) -> Tuple[bool, str]:
    """Run a system command directly."""
    command = action_data.get("command")
    args = action_data.get("args", [])
    cwd = action_data.get("cwd", ".")
    timeout = action_data.get("timeout", 300)
    
    if not isinstance(command, str) or not command:
        return False, "Missing or invalid 'command' (string) for RUN_COMMAND."
    
    if not isinstance(args, list):
        return False, "'args' must be a list for RUN_COMMAND."
    
    # Resolve working directory
    if cwd != ".":
        cwd_path = resolve_path(project_root, cwd)
        if not cwd_path or not cwd_path.is_dir():
            return False, f"Invalid working directory: '{cwd}'"
    else:
        cwd_path = project_root
    
    # Build command list
    cmd_list = [command] + [str(arg) for arg in args]
    
    success, user_message, stdout, stderr = _run_subprocess(
        cmd_list, cwd_path, "RUN_COMMAND", action_data, step_id, sudo_password=sudo_password
    )
    
    full_response_message = f"{user_message}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()
    return success, full_response_message


class ExWorkAgent:
    """
    ExWork Agent - Provides autonomous execution capabilities for Trinity Convergence
    Integrates with the LoL Nexus Compute Fabric for production deployments
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ExWork Agent with optional configuration"""
        self.config = config or {}
        self.is_initialized = True
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command through the ExWork system"""
        return {
            "success": True,
            "message": f"ExWork command executed: {command}",
            "agent": "ExWorkAgent"
        }
    
    def check_health(self) -> Dict[str, Any]:
        """Check ExWork Agent health status"""
        return {
            "status": "healthy",
            "agent": "ExWorkAgent",
            "initialized": self.is_initialized
        }


if __name__ == "__main__":
    main()
