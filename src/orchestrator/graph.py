from __future__ import annotations

"""
Agent execution graph — defines the DAG of agent dependencies.

Currently implements a simple linear sequence. Future versions will support
parallel execution and conditional branching via LangGraph or similar.

# TODO: Replace with LangGraph StateGraph when ready for production
"""

from typing import Any


class AgentGraph:
    """
    Simple agent execution graph.

    For v0.1, this is a linear sequence. Future versions will implement:
    - Parallel agent execution
    - Conditional branching based on scan results
    - Human-in-the-loop gates for OSS advisory
    """

    def __init__(self):
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[tuple[str, str]] = []

    def add_node(self, name: str, agent: Any):
        """Add an agent node to the graph."""
        self.nodes.append({"name": name, "agent": agent})

    def add_edge(self, from_node: str, to_node: str):
        """Add a directed edge between two nodes."""
        self.edges.append((from_node, to_node))

    def get_execution_order(self) -> list[str]:
        """Return the execution order (linear for now)."""
        return [node["name"] for node in self.nodes]

    def to_dict(self) -> dict:
        """Serialize the graph for debugging/visualization."""
        return {
            "nodes": [n["name"] for n in self.nodes],
            "edges": self.edges,
        }
