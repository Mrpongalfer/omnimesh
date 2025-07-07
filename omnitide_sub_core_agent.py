#!/usr/bin/env python3
import argparse
import base64
import datetime
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
import uuid
import binascii
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv
import requests
import threading

try:
    from nexus_grpc_client import NexusPrimeClient
except ImportError:
    NexusPrimeClient = None
    logger.warning("NexusPrimeClient not available. gRPC integration will be disabled.")

# Omnitide_Sub_Core_Agent: Executes structured JSON commands with AI-driven self-improvement features.
# Version: 1.0 (Refactored and Enhanced for Omnitide Nexus)

# --- Load environment variables from .env file ---
load_dotenv()

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Omnitide-SCA] [%(levelname)-7s] %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("OmnitideSCA_V1.0")

# --- Configuration ---
AGENT_ROOT_DIR = Path.cwd().resolve()
HISTORY_FILE = AGENT_ROOT_DIR / ".omnitide_sca_history.jsonl"
INSTRUCTION_FILE_POLL = AGENT_ROOT_DIR / "instructions.json"
OUTPUT_FILE_POLL = AGENT_ROOT_DIR / "results.json"
DEFAULT_OLLAMA_ENDPOINT_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma:2b")

# --- Global State ---
_pending_signoffs: Dict[str, Dict[str, Any]] = {}
ACTION_HANDLERS: Dict[str, Callable[[Dict, Path, str, bool], Tuple[bool, Any]]] = {}

# --- Helper Functions ---
def run_as_root_or_current_user(command: List[str], use_sudo: bool, cwd: Path, action_name: str, action_params: Dict, step_id: str, timeout: int = 300) -> Tuple[bool, str, str, str]:
    if use_sudo:
        full_command = ["sudo", "-n"] + command
    else:
        full_command = command
    command_str_for_log = " ".join(shlex.quote(c) for c in full_command)
    logger.info(f"Running {action_name} {'(sudo)' if use_sudo else ''}: {command_str_for_log} in CWD={cwd}")
    stdout_str = ""
    stderr_str = ""
    exit_code = -1
    user_message = ""
    success = False
    start_time = time.time()
    try:
        process = subprocess.run(
            full_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        stdout_str = process.stdout.strip() if process.stdout else ""
        stderr_str = process.stderr.strip() if process.stderr else ""
        exit_code = process.returncode
        if exit_code == 0:
            success = True
            user_message = f"{action_name} completed successfully."
            logger.info(f"Finished {action_name}. Code: {exit_code}\n--- STDOUT ---\n{stdout_str if stdout_str else '<empty>'}")
            if stderr_str:
                logger.warning(f"--- STDERR (RC=0 but stderr present) ---\n{stderr_str}")
        else:
            success = False
            user_message = f"{action_name} failed (Code: {exit_code})."
            logger.error(f"Finished {action_name}. Code: {exit_code}\n--- STDOUT ---\n{stdout_str if stdout_str else '<empty>'}\n--- STDERR ---\n{stderr_str if stderr_str else '<empty>'}")
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
            "command": command_str_for_log,
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

def resolve_path(base_path: Path, requested_path: str) -> Optional[Path]:
    try:
        if not isinstance(requested_path, str) or not requested_path.strip():
            logger.error("Requested path is empty or not a string.")
            return None
        normalized_req_path = requested_path.replace("\\", "/")
        if Path(normalized_req_path).is_absolute():
            resolved_path = Path(normalized_req_path).resolve()
            if not str(resolved_path).startswith(str(base_path)):
                logger.error(f"Absolute path '{requested_path}' resolves outside '{base_path}'. Rejected.")
                return None
        else:
            candidate_path = base_path / normalized_req_path
            resolved_path = candidate_path.resolve()
            if not str(resolved_path).startswith(str(base_path)):
                logger.error(f"Path traversal with '..' detected or resolved path '{resolved_path}' outside '{base_path}'. Rejected.")
                return None
        logger.debug(f"Resolved path '{requested_path}' to '{resolved_path}' relative to '{base_path}'")
        return resolved_path
    except Exception as e:
        logger.error(f"Error resolving path '{requested_path}' relative to '{base_path}': {e}", exc_info=True)
        return None

def log_execution_history(record: Dict[str, Any]):
    record_final = {
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action_name": record.get("action_name", "UNKNOWN_ACTION"),
        "command": record.get("command", "N/A"),
        "cwd": str(record.get("cwd", AGENT_ROOT_DIR)),
        "success": record.get("success", False),
        "exit_code": record.get("exit_code", -1),
        "stdout_snippet": str(record.get("stdout_snippet", ""))[:1000] + ("..." if len(str(record.get("stdout_snippet", ""))) > 1000 else ""),
        "stderr_snippet": str(record.get("stderr_snippet", ""))[:1000] + ("..." if len(str(record.get("stderr_snippet", ""))) > 1000 else ""),
        "message": record.get("message", ""),
        "duration_s": round(record.get("duration_s", 0.0), 3),
        "step_id": record.get("step_id", "N/A"),
        "action_params": record.get("action_params", {}),
    }
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_final) + "\n")
    except Exception as e:
        logger.error(f"Failed to log execution history for action '{record_final['action_name']}': {e}")

def handler(name: str, version: Optional[str] = None):
    def decorator(func: Callable[[Dict, Path, str, bool], Tuple[bool, Any]]):
        handler_key = f"{name}:{version}" if version else name
        ACTION_HANDLERS[handler_key] = func
        logger.debug(f"Registered action handler for: {handler_key}")
        return func
    return decorator

# --- Action Handlers ---
@handler(name="ECHO")
def handle_echo(action_data, project_root, step_id, use_sudo):
    message = action_data.get("message", "No message provided for ECHO.")
    print(f"[OMNITIDE_SCA_ECHO_STDOUT] {message}")
    logger.info(f"ECHO: {message}")
    return True, f"Echoed: {message}"

# --- Main Loop ---
def main_loop_polling():
    logger.info("Starting Omnitide Sub-Core Agent in continuous polling mode...")
    logger.info(f"Polling for instructions at: {INSTRUCTION_FILE_POLL}")
    logger.info(f"Writing results to: {OUTPUT_FILE_POLL}")
    global AGENT_ROOT_DIR
    AGENT_ROOT_DIR = Path.cwd().resolve()
    check_dependencies()
    # --- gRPC registration and status loop ---
    grpc_client = None
    if NexusPrimeClient is not None:
        grpc_client = NexusPrimeClient()
        grpc_client.register_agent()
        grpc_client.run_status_loop(interval=30)
        logger.info("gRPC client registered and status loop started.")
    else:
        logger.warning("gRPC client not available. Skipping registration and status updates.")
    while True:
        try:
            if INSTRUCTION_FILE_POLL.exists() and INSTRUCTION_FILE_POLL.is_file():
                logger.info(f"New instruction file found: {INSTRUCTION_FILE_POLL}")
                instruction_json = INSTRUCTION_FILE_POLL.read_text(encoding="utf-8")
                overall_success, action_results = process_instruction_block(
                    instruction_json, AGENT_ROOT_DIR
                )
                output_payload = {
                    "overall_success": overall_success,
                    "status_message": "Instruction block processed.",
                    "action_results": action_results,
                    "timestamp_processed": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                OUTPUT_FILE_POLL.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
                logger.info(f"Results written to: {OUTPUT_FILE_POLL}")
                INSTRUCTION_FILE_POLL.unlink(missing_ok=True)
                logger.info("Instruction file cleaned up.")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in main polling loop: {e}", exc_info=True)
            time.sleep(10)

def check_dependencies():
    logger.info("Checking Omnitide Sub-Core Agent dependencies...")
    required_packages = ["python-dotenv", "requests"]
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing_packages.append(pkg)
    if missing_packages:
        logger.warning(f"Missing Python packages: {', '.join(missing_packages)}. Attempting to install...")
        install_cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
        success, msg, _, _ = run_as_root_or_current_user(install_cmd, True, AGENT_ROOT_DIR, "INSTALL_PYTHON_DEPS", {"packages": missing_packages}, "dep_check")
        if not success:
            logger.error(f"Failed to install Python dependencies: {msg}. Agent may not function correctly.")
            print(f"[OMNITIDE_SCA_ERROR] Failed to install Python dependencies: {msg}")
    required_commands = ["sudo", "patch"]
    missing_commands = []
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing_commands.append(cmd)
    if missing_commands:
        logger.warning(f"Missing system commands: {', '.join(missing_commands)}. Some actions may fail.")
        print(f"[OMNITIDE_SCA_WARNING] Missing system commands: {', '.join(missing_commands)}. Please ensure they are installed and in PATH.")
    ollama_health_endpoint = f"{DEFAULT_OLLAMA_ENDPOINT_BASE.rstrip('/')}/api/tags"
    try:
        response = requests.get(ollama_health_endpoint, timeout=5)
        response.raise_for_status()
        models_info = response.json()
        logger.info(f"Ollama endpoint reachable. Available models: {[m['name'] for m in models_info.get('models', [])]}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama endpoint '{DEFAULT_OLLAMA_ENDPOINT_BASE}' not reachable or unhealthy: {e}. LLM actions will fail.")
        print(f"[OMNITIDE_SCA_ERROR] Ollama LLM endpoint not reachable. Ensure Ollama is running and accessible: {e}")

def process_instruction_block(instruction_json: str, project_root: Path) -> Tuple[bool, List[Dict[str, Any]]]:
    action_results_summary: List[Dict[str, Any]] = []
    overall_block_success = True
    current_step_id = str(uuid.uuid4())
    try:
        instruction = json.loads(instruction_json)
    except json.JSONDecodeError as e:
        logger.error(f"FATAL: JSON Decode Failed for instruction block: {e}")
        logger.error(f"Raw input snippet: {instruction_json[:500]}...")
        action_results_summary.append({
            "action_type": "BLOCK_PARSE",
            "success": False,
            "message_or_payload": f"JSON Decode Error: {e}",
            "step_id": current_step_id,
        })
        return False, action_results_summary
    if not isinstance(instruction, dict):
        logger.error("FATAL: Instruction block is not a JSON object.")
        action_results_summary.append({
            "action_type": "BLOCK_VALIDATION",
            "success": False,
            "message_or_payload": "Instruction block not a dict.",
            "step_id": current_step_id,
        })
        return False, action_results_summary
    step_id_from_instruction = instruction.get("step_id", current_step_id)
    description = instruction.get("description", "N/A")
    actions = instruction.get("actions", [])
    use_sudo_block_level = instruction.get("use_sudo_for_block", False)
    logger.info(f"Processing Instruction Block - StepID: {step_id_from_instruction}, Desc: {description}, Sudo for Block: {use_sudo_block_level}")
    if not isinstance(actions, list):
        logger.error(f"'{step_id_from_instruction}': 'actions' field must be a list.")
        action_results_summary.append({
            "action_type": "BLOCK_VALIDATION",
            "success": False,
            "message_or_payload": "'actions' field not a list.",
            "step_id": step_id_from_instruction,
        })
        return False, action_results_summary
    for i, action_data in enumerate(actions):
        action_num = i + 1
        action_type_value = action_data.get("type")
        use_sudo_for_action = action_data.get("use_sudo", use_sudo_block_level)
        handler = None
        current_action_type_for_log = "UNKNOWN_OR_INVALID_TYPE"
        if isinstance(action_type_value, str):
            current_action_type_for_log = action_type_value
            handler = ACTION_HANDLERS.get(current_action_type_for_log)
            if not handler:
                logger.error(f"'{step_id_from_instruction}': Action {action_num} - Unknown action type encountered: '{current_action_type_for_log}'.")
                action_results_summary.append({
                    "action_type": current_action_type_for_log,
                    "success": False,
                    "message_or_payload": f"Unknown action type: '{current_action_type_for_log}'.",
                    "action_index": i,
                    "step_id": step_id_from_instruction,
                })
                overall_block_success = False
                break
        else:
            logger.error(f"'{step_id_from_instruction}': Action {action_num} has missing or invalid 'type' (expected string, got: {type(action_type_value).__name__}).")
            action_results_summary.append({
                "action_type": str(action_type_value) if action_type_value is not None else "MISSING_TYPE",
                "success": False,
                "message_or_payload": f"Action has missing or invalid 'type': {action_type_value}",
                "action_index": i,
                "step_id": step_id_from_instruction,
            })
            overall_block_success = False
            break
        logger.info(f"--- {step_id_from_instruction}: Action {action_num}/{len(actions)} (Type: {current_action_type_for_log}, Sudo: {use_sudo_for_action}) ---")
        action_start_time = time.time()
        success, result_payload = handler(action_data, project_root, step_id_from_instruction, use_sudo_for_action)
        action_duration = time.time() - action_start_time
        action_summary = {
            "action_type": current_action_type_for_log,
            "success": success,
            "message_or_payload": result_payload,
            "duration_s": round(action_duration, 3),
            "action_index": i,
            "step_id": step_id_from_instruction,
        }
        action_results_summary.append(action_summary)
        if not success:
            logger.error(f"'{step_id_from_instruction}': Action {action_num} ({current_action_type_for_log}) FAILED. Result: {result_payload}")
            overall_block_success = False
            break
        else:
            logger.info(f"'{step_id_from_instruction}': Action {action_num} ({current_action_type_for_log}) SUCCEEDED. Duration: {action_duration:.3f}s")
    logger.info(f"--- Finished processing actions for StepID: {step_id_from_instruction}. Overall Block Success: {overall_block_success} ---")
    return overall_block_success, action_results_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Omnitide Sub-Core Agent CLI")
    parser.add_argument("--listen", action="store_true", help="Start agent in continuous polling mode.")
    parser.add_argument("--process-once", type=str, help="Process a single JSON instruction block from a file.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set log level.")
    args = parser.parse_args()
    logger.setLevel(args.log_level.upper())
    try:
        if args.listen:
            main_loop_polling()
        elif args.process_once:
            instruction_file = Path(args.process_once)
            if not instruction_file.is_file():
                logger.error(f"Instruction file not found: {instruction_file}")
                sys.exit(1)
            check_dependencies()
            json_input = instruction_file.read_text(encoding="utf-8")
            overall_success, action_results = process_instruction_block(json_input, AGENT_ROOT_DIR)
            output_payload = {
                "overall_success": overall_success,
                "status_message": "Single instruction block processed.",
                "action_results": action_results,
                "timestamp_processed": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            sys.stdout.write(json.dumps(output_payload, indent=2) + "\n")
            sys.stdout.flush()
            if not overall_success:
                sys.exit(1)
        else:
            logger.info("Omnitide Sub-Core Agent: No mode specified. Use --listen or --process-once.")
            parser.print_help()
            sys.exit(0)
    except Exception as e:
        logger.critical(f"Omnitide Sub-Core Agent encountered a critical error: {e}", exc_info=True)
        sys.stdout.write(json.dumps({"overall_success": False, "status_message": f"Critical agent error: {e}"}) + "\n")
        sys.exit(1)
    logger.info("Omnitide Sub-Core Agent gracefully completed or stopped.")
