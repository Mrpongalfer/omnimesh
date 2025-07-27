# agent_ex_work/models/results.py
# Defines the ActionResult and OverallResult data structures for Agent Ex-Work.

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import os
from pathlib import Path
import logging

class ActionResult(BaseModel):
    """
    Represents the result of a single executed action.
    """
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    action_type: str
    action_id: str
    duration_seconds: Optional[float] = None
    timestamp: datetime = datetime.now()
    payload: Dict[str, Any] = {}

class OverallResult(BaseModel):
    """
    Represents the overall result of executing an entire InstructionBlock.
    """
    overall_success: bool
    status_message: str
    total_duration_seconds: float
    action_results: List[ActionResult] = []
    timestamp: datetime = datetime.now()
    instruction_block_id: str = ""
    transaction_id: str = ""
    source_actor: str = ""

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode='json')

    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        return cls.model_validate(data)

    def save_to_history(self, history_file_path: Path):
        """
        Appends this overall result to a JSONL history file.
        This provides an audit trail for autonomous operations.
        Derived from `awesome-logging`, `awesome-security-auditing`.
        """
        try:
            history_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_file_path, 'a') as f:
                f.write(json.dumps(self.to_json()) + '\n')
            logging.info(f"Execution history saved to: {history_file_path}")
        except Exception as e:
            logging.error(f"Failed to save execution history to {history_file_path}: {e}")
