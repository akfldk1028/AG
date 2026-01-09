/**
 * Selector Pattern (SelectorGroupChat)
 *
 * Layout: Hub-and-Spoke
 *         User → Selector (center) → Agent1, Agent2, Agent3... (around)
 *
 * - Central selector/router node
 * - Agents arranged in semi-circle around selector
 * - Selector chooses best agent for each task
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

const CENTER_X = 350;
const CENTER_Y = 150;
const RADIUS = 200;

export const generateSelectorLayout = (
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

  // Create user node to the left
  nodes.push(
    createUserNode(
      {
        x: CENTER_X - 300,
        y: CENTER_Y - NODE_DIMENSIONS.default.height / 2,
      },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // Create central selector node
  nodes.push(
    createAgentNode(
      "selector-hub",
      "Selector",
      "Router",
      "Selects best agent for task",
      {
        x: CENTER_X - NODE_DIMENSIONS.default.width / 2,
        y: CENTER_Y - NODE_DIMENSIONS.default.height / 2,
      },
      true, // Selector is always active when team is running
      isProcessing
    )
  );

  // Edge from user to selector
  edges.push(
    createEdge("user-to-selector", "user", "selector-hub", {
      stroke: "#2563eb",
      strokeWidth: 2,
      animated: participatedAgents.size > 0,
    })
  );

  // Create agent nodes in semi-circle around selector
  participants.forEach((p: Component<AgentConfig>, index: number) => {
    const agentName = p.config?.name || `agent-${index}`;
    // Spread agents from -60° to +60° (semi-circle on the right)
    const startAngle = -Math.PI / 3; // -60 degrees
    const endAngle = Math.PI / 3; // +60 degrees
    const angleStep = (endAngle - startAngle) / Math.max(1, participants.length - 1);
    const angle = participants.length === 1
      ? 0 // Single agent goes straight right
      : startAngle + index * angleStep;

    const x = CENTER_X + RADIUS * Math.cos(angle);
    const y = CENTER_Y + RADIUS * Math.sin(angle);

    nodes.push(
      createAgentNode(
        agentName,
        agentName,
        p.label || "",
        p.description || "",
        {
          x: x - NODE_DIMENSIONS.default.width / 2,
          y: y - NODE_DIMENSIONS.default.height / 2,
        },
        participatedAgents.has(agentName),
        isProcessing
      )
    );

    // Edge from selector to each agent
    const isAgentActive = participatedAgents.has(agentName);
    edges.push(
      createEdge(`selector-to-${agentName}`, "selector-hub", agentName, {
        animated: isAgentActive,
        stroke: isAgentActive ? "#22c55e" : "#6b7280",
        strokeWidth: isAgentActive ? 2 : 1,
        opacity: isAgentActive ? 1 : 0.4,
      })
    );

    // Return edge from agent back to selector (for multi-turn conversations)
    edges.push(
      createEdge(`${agentName}-to-selector`, agentName, "selector-hub", {
        stroke: isAgentActive ? "#f59e0b" : "#6b7280",
        strokeWidth: 1,
        strokeDasharray: "5,5",
        opacity: isAgentActive ? 0.7 : 0.2,
        routingType: "secondary",
      })
    );
  });

  // Add end node if run is complete
  if (isComplete) {
    nodes.push(
      createEndNode(
        {
          x: CENTER_X + RADIUS + 100,
          y: CENTER_Y - NODE_DIMENSIONS.end.height / 2,
        },
        run
      )
    );

    // Find the last participating agent to connect to end
    const lastActiveAgent = [...participatedAgents].filter(
      (a) => a !== "user" && a !== "selector-hub"
    ).pop();

    if (lastActiveAgent) {
      edges.push(
        createEdge(`${lastActiveAgent}-to-end`, lastActiveAgent, "end", {
          stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
          strokeWidth: 2,
          label: "ended",
        })
      );
    } else {
      // Connect selector directly to end if no agent was selected
      edges.push(
        createEdge("selector-to-end", "selector-hub", "end", {
          stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
          strokeWidth: 2,
          label: "ended",
        })
      );
    }
  }

  return { nodes, edges };
};
