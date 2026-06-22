"""
Project context manager for large-project agent workflows.

Collects and injects relevant context (cwd, files, previous results)
into agent prompts. Integrates with SharedMemory (port 8101).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class ProjectContext:
    """Project context information passed to SDK agents."""
    cwd: str
    project_name: str = ""
    relevant_files: List[str] = field(default_factory=list)
    previous_results: Dict[str, str] = field(default_factory=dict)
    shared_memory: Dict[str, object] = field(default_factory=dict)


class ContextManager:
    """Collect and inject project context for agent prompts."""

    SHARED_MEMORY_URL = "http://localhost:8101"

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def build_context(
        self,
        task_description: str = "",
        relevant_files: Optional[List[str]] = None,
        previous_results: Optional[Dict[str, str]] = None,
    ) -> ProjectContext:
        """
        Build a ProjectContext from project root and optional hints.

        Args:
            task_description: Free-text task description (for future auto-discovery).
            relevant_files: Explicit list of file paths to include.
            previous_results: Dict mapping stage names to their outputs.

        Returns:
            ProjectContext ready for injection.
        """
        cwd = str(self.root.resolve())
        project_name = self.root.name

        files = relevant_files or []
        if not files:
            files = self._discover_key_files()

        prev = previous_results or {}

        # Fetch shared memory data (best-effort, non-blocking)
        shared = self._fetch_shared_memory()

        return ProjectContext(
            cwd=cwd,
            project_name=project_name,
            relevant_files=files,
            previous_results=prev,
            shared_memory=shared,
        )

    def _discover_key_files(self, max_files: int = 20) -> List[str]:
        """Auto-discover key project files (README, configs, entry points)."""
        key_patterns = [
            "README.md", "CLAUDE.md", "package.json", "pyproject.toml",
            "setup.py", "requirements.txt", "Cargo.toml", "go.mod",
            "tsconfig.json", "vite.config.*", ".env.example",
        ]

        found = []
        for pattern in key_patterns:
            matches = list(self.root.glob(pattern))
            for m in matches:
                if m.is_file() and len(found) < max_files:
                    found.append(str(m.relative_to(self.root)))

        return found

    def _fetch_shared_memory(self) -> Dict[str, object]:
        """Fetch data from SharedMemory server (port 8101). Best-effort."""
        try:
            import urllib.request
            url = f"{self.SHARED_MEMORY_URL}/events"
            req = urllib.request.Request(url, method="GET")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, dict) else {"events": data}
        except Exception:
            return {}

    @staticmethod
    def inject_to_prompt(context: ProjectContext, base_prompt: str) -> str:
        """
        Inject context into prompt text.

        Prepends project info, previous results, and file references
        before the base prompt.
        """
        sections = []

        # Project info
        if context.project_name:
            sections.append(f"[Project: {context.project_name}]")

        # Previous stage results
        if context.previous_results:
            sections.append("=== Previous Stage Results ===")
            for stage_name, output in context.previous_results.items():
                # Truncate very long outputs
                truncated = output[:4000] + "..." if len(output) > 4000 else output
                sections.append(f"\n[{stage_name}]:\n{truncated}")
            sections.append("=== End Previous Results ===\n")

        # Relevant file references
        if context.relevant_files:
            file_list = ", ".join(context.relevant_files[:10])
            sections.append(f"[Relevant files: {file_list}]")

        if sections:
            prefix = "\n".join(sections) + "\n\n"
            return prefix + base_prompt

        return base_prompt
