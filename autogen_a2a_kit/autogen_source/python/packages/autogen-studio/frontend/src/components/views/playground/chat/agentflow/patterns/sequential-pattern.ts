/**
 * Sequential Pattern (RoundRobinGroupChat)
 *
 * Layout: User → Agent1 → Agent2 → Agent3 → ... → End
 * - Linear horizontal flow
 * - Agents take turns in fixed order defined by participants array
 */

import { Node } from "@xyflow/react";
import {
  Component,
  AgentConfig,
  TeamConfig,
  Run,
} from "../../../../../types/datamodel";
import { CustomEdge } from "../edge";
import {
  PatternLayoutResult,
  NODE_DIMENSIONS,
  createAgentNode,
  createUserNode,
  createEndNode,
  createEdge,
} from "./types";

const HORIZONTAL_SPACING = 200;

export const generateSequentialLayout = (
  teamConfig: Component<TeamConfig>,
  participatedAgents: Set<string>,
  run?: Run
): PatternLayoutResult => {
  const participants = teamConfig.config?.participants || [];
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];
  const isProcessing =
    run?.status === "active" || run?.status === "awaiting_input";
  const isComplete = ["complete", "error", "stopped"].includes(
    run?.status || ""
  );

  // Create user node at the start
  nodes.push(
    createUserNode({ x: 0, y: 0 }, participatedAgents.has("user"), isProcessing)
  );

  // Create agent nodes in sequence
  participants.forEach((p: Component<AgentConfig>, index: number) => {
    const agentName = p.config?.name || `agent-${index}`;
    const xPos = (index + 1) * HORIZONTAL_SPACING;

    nodes.push(
      createAgentNode(
        agentName,
        agentName,
        p.label || "",
        p.description || "",
        { x: xPos, y: 0 },
        participatedAgents.has(agentName),
        isProcessing
      )
    );
  });

  // Create edges: User → Agent1
  if (participants.length > 0) {
    const firstAgentName = participants[0]?.config?.name || "agent-0";
    edges.push(
      createEdge("user-to-first", "user", firstAgentName, {
        animated: participatedAgents.has(firstAgentName),
        stroke: participatedAgents.has(firstAgentName) ? "#22c55e" : "#6b7280",
        strokeWidth: participatedAgents.has(firstAgentName) ? 2 : 1,
        opacity: participatedAgents.has(firstAgentName) ? 1 : 0.5,
      })
    );
  }

  // Create edges between agents: Agent1 → Agent2 → Agent3 → ...
  for (let i = 0; i < participants.length - 1; i++) {
    const sourceName = participants[i]?.config?.name || `agent-${i}`;
    const targetName = participants[i + 1]?.config?.name || `agent-${i + 1}`;
    const isActive =
      participatedAgents.has(sourceName) && participatedAgents.has(targetName);

    edges.push(
      createEdge(`${sourceName}-to-${targetName}`, sourceName, targetName, {
        animated: isActive,
        stroke: isActive ? "#22c55e" : "#6b7280",
        strokeWidth: isActive ? 2 : 1,
        opacity: isActive ? 1 : 0.5,
      })
    );
  }

  // Add loop back edge (last agent → first agent) for continuous round-robin
  if (participants.length > 1) {
    const lastAgentName =
      participants[participants.length - 1]?.config?.name ||
      `agent-${participants.length - 1}`;
    const firstAgentName = participants[0]?.config?.name || "agent-0";

    edges.push(
      createEdge(`${lastAgentName}-loop-to-${firstAgentName}`, lastAgentName, firstAgentName, {
        stroke: "#6b7280",
        strokeWidth: 1,
        strokeDasharray: "5,5",
        opacity: 0.3,
        label: "loop",
      })
    );
  }

  // Add end node if run is complete
  if (isComplete && participants.length > 0) {
    const lastAgentName =
      participants[participants.length - 1]?.config?.name ||
      `agent-${participants.length - 1}`;
    const endX = (participants.length + 1) * HORIZONTAL_SPACING;

    nodes.push(createEndNode({ x: endX, y: 0 }, run));

    edges.push(
      createEdge(`${lastAgentName}-to-end`, lastAgentName, "end", {
        stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
        strokeWidth: 2,
        label: "ended",
      })
    );
  }

  return { nodes, edges };
};
