#!/usr/bin/env python3
"""
Resource Tracker Module
Tracks all YouTube API calls and NotebookLM operations for debugging, cost monitoring, and audit.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class ResourceTracker:
    """Resource tracking and logging system"""

    def __init__(self, log_file: str = "youtube_research_flow/resource_log.json"):
        self.log_file = log_file
        self.session_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        self._init_log()

    def _init_log(self):
        """Initialize or load resource tracking log"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    try:
                        self.log_data = json.load(f)
                    except json.JSONDecodeError:
                        self.log_data = {"session_id": self.session_id, "operations": []}
            else:
                self.log_data = {
                    "session_id": self.session_id,
                    "operations": []
                }
        except Exception as e:
            print(f"❌ Failed to initialize resource log: {e}")
            self.log_data = {"session_id": self.session_id, "operations": []}

    def _save_log(self):
        """Save resource tracking log to file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Failed to save resource log: {e}")

    def log_operation(
        self,
        operation_type: str,  # 'search', 'create_notebook', 'import_source', etc.
        resource_type: str,  # 'youtube_api', 'notebooklm', 'file'
        details: Dict[str, Any]  # Operation-specific data
    ) -> None:
        """Log a resource operation"""
        operation = {
            "operation_type": operation_type,
            "resource_type": resource_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }

        self.log_data["operations"].append(operation)
        self._save_log()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage"""
        youtube_calls = len([op for op in self.log_data["operations"] if op["resource_type"] == "youtube_api"])
        notebooklm_ops = len([op for op in self.log_data["operations"] if op["resource_type"] == "notebooklm"])
        videos_retrieved = sum(op["details"].get("results_count", 0) for op in self.log_data["operations"] if op["operation_type"] == "search")

        return {
            "session_id": self.session_id,
            "total_operations": len(self.log_data["operations"]),
            "youtube_api_calls": youtube_calls,
            "notebooklm_operations": notebooklm_ops,
            "videos_retrieved": videos_retrieved,
            "analysis_generated": len([op for op in self.log_data["operations"] if op["operation_type"] == "generate_analysis"]),
            "deliverables_created": len([op for op in self.log_data["operations"] if op["operation_type"] == "create_deliverable"])
        }


if __name__ == "__main__":
    # Demo usage
    tracker = ResourceTracker()
    tracker.log_operation("session_start", "session", {"query": "YouTube Research Demo"})
    tracker.log_operation("search", "youtube_api", {
        "query": "榴莲测评",
        "results_count": 10,
        "params": {"max_results": 10, "time_range": "6 months"}
    })

    summary = tracker.get_summary()
    print("Resource Tracking Demo")
    print(f"Session ID: {summary['session_id']}")
    print(f"Total operations: {summary['total_operations']}")
    print(f"YouTube API calls: {summary['youtube_api_calls']}")
    print(f"Videos retrieved: {summary['videos_retrieved']}")
    print("\nResource tracking log saved to: youtube_research_flow/resource_log.json")
