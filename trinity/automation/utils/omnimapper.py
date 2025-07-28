#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import hashlib
import sys
from typing import List, Optional, Dict, Any
import re # Added for regex in scan_directory exclusions
import logging # <-- ADDED THIS IMPORT

# omnimapper.py - OMNIMESH Reconnaissance Script
# Generates a structured overview of a large codebase for AI analysis.

def calculate_sha256(filepath: Path, chunk_size: int = 4096) -> Optional[str]:
    """Calculates the SHA256 hash of a file."""
    try:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.warning(f"Failed to calculate SHA256 for {filepath}: {e}")
        return None

def get_file_details(filepath: Path, project_root: Path, max_snippet_lines: int = 20) -> Dict[str, Any]:
    """
    Extracts details from a file, including a head and tail snippet.
    Also attempts to infer basic file type.
    """
    try:
        relative_path = str(filepath.relative_to(project_root))
        
        file_stats = filepath.stat()
        file_size_bytes = file_stats.st_size
        file_mtime = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        
        file_type = "unknown"
        content_lines = []
        
        # Determine if file is likely text or binary without reading fully
        is_text_heuristic = True
        try:
            # Check for common text file extensions
            text_extensions = {'.py', '.sh', '.json', '.yml', '.yaml', '.env', '.md', '.txt', '.xml', '.html', '.css', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.c', '.cpp', '.h', '.hpp', '.php', '.rb', '.pl', '.config', '.ini', '.toml', '.csv', '.log', '.sql', '.vue', '.svelte', '.rs'}
            if filepath.suffix.lower() in text_extensions:
                file_type = filepath.suffix.lower().lstrip('.') + "_code_or_config"
            elif filepath.name.lower() == 'dockerfile':
                file_type = "dockerfile"
            
            # Attempt to read a small part to check for null bytes
            with open(filepath, 'rb') as f:
                header = f.read(1024) # Read first 1KB
                if b'\x00' in header and file_size_bytes > 0: # Presence of null byte suggests binary, unless it's a zero-byte file
                    is_text_heuristic = False
        except Exception:
            is_text_heuristic = False # Assume binary if we can't even read a header

        if not is_text_heuristic:
            file_type = "binary" if file_size_bytes > 0 else "empty"
            # For large binary files, categorize more specifically
            if file_size_bytes > 5 * 1024 * 1024: # 5MB threshold for large binary
                file_type = "binary_large"
            elif file_size_bytes > 0:
                file_type = "binary_small"
        else:
            # If it's likely text, try to read full content for snippets and more specific type
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content_lines = f.readlines()
                
                # Refine type based on content/filename if not already set by extension
                suffix = filepath.suffix.lower()
                if suffix == '.py' and "python_script" not in file_type: file_type = "python_script"
                elif suffix == '.sh' and "shell_script" not in file_type: file_type = "shell_script"
                elif suffix == '.json' and "json_config_data" not in file_type: file_type = "json_config_data"
                elif suffix == '.yml' or suffix == '.yaml' and "yaml_config" not in file_type: file_type = "yaml_config"
                elif suffix == '.env' and "env_variables" not in file_type: file_type = "env_variables"
                elif filepath.name.lower() == 'dockerfile' and "dockerfile" not in file_type: file_type = "dockerfile"
                elif suffix == '.md' and "markdown_document" not in file_type: file_type = "markdown_document"
                elif suffix == '.txt' and "text_file" not in file_type: file_type = "text_file"
                elif "code_or_config" not in file_type: # General text file if no specific code/config suffix
                    file_type = "text_file"

            except Exception as e:
                logging.warning(f"Could not read {filepath} as text for snippets despite heuristic: {e}")
                file_type = "unreadable_text" if file_size_bytes > 0 else "empty" # Fallback if text read fails

        head_snippet = "".join(content_lines[:max_snippet_lines]) if content_lines else None
        tail_snippet = "".join(content_lines[-max_snippet_lines:]) if len(content_lines) > max_snippet_lines * 2 else None

        # Attempt to infer role/functionality based on filename/path/content
        inferred_role = "general_file"
        filename_lower = filepath.name.lower()
        
        # Priority order for role inference based on common project structures
        if "main" in filename_lower and "entrypoint" not in inferred_role: inferred_role = "main_application_entrypoint"
        if "app" in filename_lower and "entrypoint" not in inferred_role: inferred_role = "application_entrypoint"
        if "start" in filename_lower or "run" in filename_lower: inferred_role = "launcher/runner"
        if "deploy" in filename_lower or "setup" in filename_lower: inferred_role = "deployment/setup"
        if "agent" in filename_lower or "worker" in filename_lower or "service" in filename_lower: inferred_role = "agent/service"
        if "config" in filename_lower or "env" in filename_lower or ".toml" in filename_lower or ".ini" in filename_lower or "settings" in filename_lower: inferred_role = "configuration"
        if "test" in filename_lower or "spec" in filename_lower or "mock" in filename_lower: inferred_role = "testing"
        if "heal" in filename_lower or "fix" in filename_lower or "clean" in filename_lower: inferred_role = "maintenance/healing"
        if "metamorphosis" in filename_lower or "evolve" in filename_lower: inferred_role = "self_improvement_orchestration"
        if "nexus" in filename_lower or "bridge" in filename_lower: inferred_role = "core_communication/integration"
        if "vectorize" in filename_lower or "embed" in filename_lower or "constitution" in filename_lower: inferred_role = "data_vectorization/knowledge_base"
        if "llm_code_generator" in filename_lower or "generate_code" in filename_lower: inferred_role = "llm_code_generation"
        if "omnimapper" in filename_lower: inferred_role = "codebase_reconnaissance"
        if "model" in filename_lower and "python_script" in file_type: inferred_role = "data_model"
        if "view" in filename_lower and "python_script" in file_type: inferred_role = "web_view"
        if "controller" in filename_lower and "python_script" in file_type: inferred_role = "web_controller"
        if "route" in filename_lower and "python_script" in file_type: inferred_role = "api_routes"
        if "database" in filename_lower or "db" in filename_lower: inferred_role = "database_interaction"
        if "api" in filename_lower: inferred_role = "api_interface"
        if "client" in filename_lower or "frontend" in filename_lower or "web" in filename_lower: inferred_role = "client_side_logic"
        if "server" in filename_lower or "backend" in filename_lower: inferred_role = "server_side_logic"
        if "handler" in filename_lower or "listener" in filename_lower: inferred_role = "event_handler"
        if "util" in filename_lower or "helper" in filename_lower or "lib" in filename_lower: inferred_role = "utility_library"
        if "component" in filename_lower or "widget" in filename_lower: inferred_role = "ui_component"
        if "style" in filename_lower or ".css" in filename_lower or ".scss" in filename_lower: inferred_role = "stylesheet"
        if "script" in filename_lower: inferred_role = "general_script"
        if "doc" in filename_lower or "readme" in filename_lower: inferred_role = "documentation"
        
        return {
            "path": relative_path,
            "filename": filepath.name,
            "type": file_type,
            "size_bytes": file_size_bytes,
            "modified_time": file_mtime,
            "sha256": calculate_sha256(filepath),
            "inferred_role": inferred_role,
            "head_snippet": head_snippet,
            "tail_snippet": tail_snippet,
            "full_content_available": True if file_type not in ["binary", "binary_large", "binary_small", "unreadable_or_binary", "empty"] else False
        }
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {e}", exc_info=True)
        return {
            "path": str(filepath.relative_to(project_root)) if filepath.is_relative_to(project_root) else str(filepath),
            "filename": filepath.name,
            "type": "error",
            "error": str(e),
            "size_bytes": filepath.stat().st_size if filepath.exists() else 0,
            "modified_time": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat() if filepath.exists() else None,
            "inferred_role": "error",
            "sha256": None,
            "head_snippet": None,
            "tail_snippet": None,
            "full_content_available": False
        }


def scan_directory(root_dir: Path, exclude_dirs: List[str], exclude_files: List[str], max_files_limit: int = 5000) -> Dict[str, Any]:
    """Recursively scans a directory and collects file details."""
    overview = {
        "scan_timestamp": datetime.now().isoformat(),
        "project_root": str(root_dir.resolve()),
        "total_files": 0,
        "total_size_bytes": 0,
        "files": []
    }
    
    # Compile regex patterns for exclusion for better performance
    # Ensure patterns match full directory names or end with / for directories
    exclude_dir_patterns = [re.compile(f"/{re.escape(d)}(/|$)") for d in exclude_dirs]
    # For files, just match the filename
    exclude_file_patterns = [re.compile(re.escape(f)) for f in exclude_files]

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        current_path_obj = Path(dirpath).resolve()
        
        # Filter dirnames in-place to skip excluded directories for os.walk
        dirnames_copy = list(dirnames) # Create a copy to iterate while modifying original
        dirnames[:] = [] # Clear original list
        for d in dirnames_copy:
            # Check if the full path of the directory relative to root matches any exclusion pattern
            try:
                full_dir_path_relative = str(Path(dirpath).relative_to(root_dir) / d)
            except ValueError: # Occurs if dirpath is root_dir and d is directly under it
                full_dir_path_relative = d
            
            if not any(pattern.search(f"/{full_dir_path_relative}") for pattern in exclude_dir_patterns):
                dirnames.append(d) # Keep this directory
            else:
                logging.info(f"Excluding directory: {full_dir_path_relative}")


        for filename in filenames:
            file_path = current_path_obj / filename
            relative_file_path_str = str(file_path.relative_to(root_dir))

            # Skip explicitly excluded files by name
            if any(pattern.match(filename) for pattern in exclude_file_patterns):
                logging.debug(f"Excluding file (explicit): {relative_file_path_str}")
                continue
            
            # Skip hidden files/directories (starting with .) except .env files
            # This check is now more robust to prevent skipping files like .bashrc within home dir if root_dir is home
            # But specific to project subdirs, we generally want to skip hidden dotfiles/dirs
            if filename.startswith('.') and filename != '.env' and not str(file_path).startswith(str(root_dir / ".git")): # Don't skip .git dir itself, its handled by exclude_dirs
                logging.debug(f"Excluding file (hidden): {relative_file_path_str}")
                continue
            
            # Skip common VCS/IDE/build dirs components (e.g., within .git, .idea, etc.)
            # This check applies to path components, not just the root
            path_parts = str(file_path.relative_to(root_dir)).split(os.sep)
            if any(part in path_parts for part in [".git", ".idea", ".vscode", "__pycache__", ".venv", "node_modules", "dist", "build", "logs"]):
                logging.debug(f"Excluding file (common dev/build): {relative_file_path_str}")
                continue

            # Limit total files to avoid overwhelming output for truly enormous repos
            if max_files_limit > 0 and overview["total_files"] >= max_files_limit:
                logging.warning(f"Reached maximum file scan limit ({overview['total_files']}). Truncating scan output for brevity. Consider increasing --max-files if needed for deeper analysis.")
                return overview # Return early to prevent excessively large output

            details = get_file_details(file_path, root_dir)
            overview["files"].append(details)
            overview["total_files"] += 1
            overview["total_size_bytes"] += details.get("size_bytes", 0)
    
    return overview

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OMNIMESH Reconnaissance Script: Scans a codebase and generates a structured overview."
    )
    parser.add_argument(
        "root_directory",
        type=str,
        help="The absolute path to the root of your OMNIMESH project.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="omnimapper_report.json",
        help="Output file name for the JSON report.",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=["__pycache__", ".venv", ".git", ".idea", ".vscode", "node_modules", "dist", "build", "logs"],
        help="Directories to exclude from scanning (e.g., .venv .git). These are matched as full directory names.",
    )
    parser.add_argument(
        "--exclude-files",
        nargs="*",
        default=[".DS_Store", "Thumbs.db"],
        help="Specific file names to exclude from scanning (e.g., .DS_Store).",
    )
    parser.add_argument(
        "--max-snippet-lines",
        type=int,
        default=20,
        help="Maximum lines for head/tail code snippets.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5000, # Default limit to prevent excessively large outputs
        help="Maximum number of files to scan for the report. Set to 0 for no limit.",
    )

    args = parser.parse_args()

    # Setup logging. Always set it up at the top level for main execution.
    # The default stream is sys.stderr.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
    logger = logging.getLogger(__name__)

    try:
        project_root = Path(args.root_directory).resolve()
        if not project_root.is_dir():
            logger.error(f"Error: Root directory not found or is not a directory: {args.root_directory}")
            sys.exit(1)

        logger.info(f"Scanning OMNIMESH project at: {project_root}")
        logger.info(f"Excluding directories: {', '.join(args.exclude_dirs)}")
        logger.info(f"Excluding files: {', '.join(args.exclude_files)}")
        logger.info(f"Max files to scan: {args.max_files if args.max_files > 0 else 'No Limit'}")

        scan_results = scan_directory(
            root_dir=project_root, 
            exclude_dirs=args.exclude_dirs, 
            exclude_files=args.exclude_files, 
            max_files_limit=args.max_files
        )

        output_path = Path(args.output_file).resolve()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scan_results, f, indent=2)

        logger.info(f"Scan complete. Report saved to: {output_path}")
        logger.info(f"Total files scanned: {scan_results['total_files']}")
        logger.info(f"Total size: {scan_results['total_size_bytes']} bytes")

    except Exception as e:
        logger.exception(f"An unexpected error occurred during scanning: {e}")
        sys.exit(1)
