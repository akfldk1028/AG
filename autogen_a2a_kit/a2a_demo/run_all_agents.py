"""
Run All A2A Agents

Starts all A2A agents for AG-ACE-BRIDGE integration.

Ports:
- poetry_agent: 8003
- philosophy_agent: 8004
- history_agent: 8005
- calculator_agent: 8006
- math_agent: 8007
- graphics_agent: 8008
- gpu_agent: 8009
- gui_test_agent: 8120

Usage:
    python run_all_agents.py           # Start all agents
    python run_all_agents.py --subset  # Start core agents only (8003-8006)
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict


# Agent configuration: name -> (port, folder)
AGENTS: Dict[str, tuple] = {
    "poetry_agent": (8003, "poetry_agent"),
    "philosophy_agent": (8004, "philosophy_agent"),
    "history_agent": (8005, "history_agent"),
    "calculator_agent": (8006, "calculator_agent"),
    "math_agent": (8007, "math_agent"),
    "graphics_agent": (8008, "graphics_agent"),
    "gpu_agent": (8009, "gpu_agent"),
    "gui_test_agent": (8120, "gui_test_agent"),
}

# Core agents (subset for quick testing)
CORE_AGENTS = ["poetry_agent", "philosophy_agent", "history_agent", "calculator_agent"]


def get_script_dir() -> Path:
    """Get the directory containing this script."""
    return Path(__file__).parent.resolve()


def start_agent(name: str, port: int, folder: str, script_dir: Path) -> subprocess.Popen:
    """
    Start a single A2A agent.

    Args:
        name: Agent name
        port: Port number
        folder: Folder containing agent.py
        script_dir: Base directory

    Returns:
        Popen process object
    """
    agent_dir = script_dir / folder
    agent_script = agent_dir / "agent.py"

    if not agent_script.exists():
        print(f"[WARN] {name}: agent.py not found at {agent_script}")
        return None

    print(f"[START] {name} on port {port}...")

    # Start agent process
    process = subprocess.Popen(
        [sys.executable, str(agent_script)],
        cwd=str(agent_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return process


def main():
    parser = argparse.ArgumentParser(description="Start A2A agents")
    parser.add_argument(
        "--subset",
        action="store_true",
        help="Start core agents only (8003-8006)"
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        help="Specific agents to start (e.g., --agents calculator_agent poetry_agent)"
    )
    args = parser.parse_args()

    script_dir = get_script_dir()
    print("=" * 60)
    print("A2A Agent Launcher")
    print("=" * 60)
    print(f"Base directory: {script_dir}")
    print()

    # Determine which agents to start
    if args.agents:
        agents_to_start = {k: v for k, v in AGENTS.items() if k in args.agents}
    elif args.subset:
        agents_to_start = {k: v for k, v in AGENTS.items() if k in CORE_AGENTS}
    else:
        agents_to_start = AGENTS

    print(f"Starting {len(agents_to_start)} agents...")
    print()

    processes: Dict[str, subprocess.Popen] = {}

    # Start all agents
    for name, (port, folder) in agents_to_start.items():
        process = start_agent(name, port, folder, script_dir)
        if process:
            processes[name] = process
            time.sleep(0.5)  # Small delay between starts

    print()
    print("=" * 60)
    print("All agents started!")
    print("=" * 60)
    print()
    print("Ports:")
    for name, (port, _) in agents_to_start.items():
        status = "RUNNING" if name in processes else "FAILED"
        print(f"  {name}: http://127.0.0.1:{port} [{status}]")

    print()
    print("Agent cards available at:")
    for name, (port, _) in agents_to_start.items():
        if name in processes:
            print(f"  http://127.0.0.1:{port}/.well-known/agent.json")

    print()
    print("Press Ctrl+C to stop all agents...")

    # Wait for all processes
    try:
        while True:
            time.sleep(1)
            # Check if any process died
            for name, proc in list(processes.items()):
                if proc.poll() is not None:
                    print(f"[DIED] {name} exited with code {proc.returncode}")
                    # Read stderr for error info
                    stderr = proc.stderr.read()
                    if stderr:
                        print(f"  Error: {stderr[:200]}")
                    del processes[name]

            if not processes:
                print("All agents stopped!")
                break

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down all agents...")
        for name, proc in processes.items():
            print(f"  Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        print("All agents stopped.")


if __name__ == "__main__":
    main()
