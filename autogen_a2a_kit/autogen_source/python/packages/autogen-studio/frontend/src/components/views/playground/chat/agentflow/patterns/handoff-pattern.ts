/**
 * Handoff Pattern (Swarm)
 *
 * Layout: Triage Center with Bidirectional Connections
 *         User → Triage (center) ⟷ Agent1, Agent2, Agent3... (around)
 *
 * - Central triage/coordinator agent (usually first agent or named "triage")
 * - Specialist agents arranged around triage
 * - Bidirectional arrows showing handoff capability
 * - Agents can dynamically transfer control to each other
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

export const generateHandoffLayout = (
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

  // Find triage/coordinator agent (usually first or named "triage")
  const triageIndex = participants.findIndex((p: Component<AgentConfig>) =>
    p.config?.name?.toLowerCase().includes("triage")
  );
  const actualTriageIndex = triageIndex >= 0 ? triageIndex : 0;
  const triageAgent = participants[actualTriageIndex];
  const triageName = triageAgent?.config?.name || "triage";
  const otherAgents = participants.filter(
    (_: Component<AgentConfig>, i: number) => i !== actualTriageIndex
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

  // Create central triage node
  nodes.push(
    createAgentNode(
      triageName,
      triageName,
      triageAgent?.label || "Triage",
      triageAgent?.description || "Routes tasks to specialists",
      {
        x: CENTER_X - NODE_DIMENSIONS.default.width / 2,
        y: CENTER_Y - NODE_DIMENSIONS.default.height / 2,
      },
      participatedAgents.has(triageName),
      isProcessing
    )
  );

  // Edge from user to triage
  edges.push(
    createEdge("user-to-triage", "user", triageName, {
      stroke: "#2563eb",
      strokeWidth: 2,
      animated: participatedAgents.has(triageName),
    })
  );

  // Create specialist agent nodes in semi-circle
  otherAgents.forEach((p: Component<AgentConfig>, index: number) => {
    const agentName = p.config?.name || `agent-${index}`;
    // Spread agents from -60° to +60° (semi-circle on the right)
    const startAngle = -Math.PI / 3;
    const endAngle = Math.PI / 3;
    const angleStep =
      otherAgents.length === 1
        ? 0
        : (endAngle - startAngle) / (otherAgents.length - 1);
    const angle = otherAgents.length === 1 ? 0 : startAngle + index * angleStep;

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

    const isAgentActive = participatedAgents.has(agentName);

    // Bidirectional edges: Triage → Agent (handoff)
    edges.push(
      createEdge(`${triageName}-to-${agentName}`, triageName, agentName, {
        animated: isAgentActive,
        stroke: isAgentActive ? "#22c55e" : "#6b7280",
        strokeWidth: isAgentActive ? 2 : 1,
        opacity: isAgentActive ? 1 : 0.4,
        label: isAgentActive ? "handoff" : "",
      })
    );

    // Agent → Triage (return)
    edges.push(
      createEdge(`${agentName}-to-${triageName}`, agentName, triageName, {
        stroke: isAgentActive ? "#f59e0b" : "#6b7280",
        strokeWidth: 1,
        strokeDasharray: "5,5",
        opacity: isAgentActive ? 0.8 : 0.2,
        routingType: "secondary",
        label: isAgentActive ? "return" : "",
      })
    );
  });

  // Add cross-agent handoff edges if agents have participated
  // (In Swarm, agents can hand off directly to each other)
  if (otherAgents.length > 1) {
    otherAgents.forEach((p1: Component<AgentConfig>, i: number) => {
      otherAgents.forEach((p2: Component<AgentConfig>, j: number) => {
        if (i !== j) {
          const agent1 = p1.config?.name || `agent-${i}`;
          const agent2 = p2.config?.name || `agent-${j}`;
          const bothActive =
            participatedAgents.has(agent1) && participatedAgents.has(agent2);

          // Only show cross-edges if both agents have participated
          if (bothActive) {
            edges.push(
              createEdge(`${agent1}-cross-to-${agent2}`, agent1, agent2, {
                stroke: "#8b5cf6", // Purple for cross-handoffs
                strokeWidth: 1,
                strokeDasharray: "3,3",
                opacity: 0.5,
              })
            );
          }
        }
      });
    });
  }

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
      (a) => a !== "user"
    ).pop();

    if (lastActiveAgent) {
      edges.push(
        createEdge(`${lastActiveAgent}-to-end`, lastActiveAgent, "end", {
          stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
          strokeWidth: 2,
          label: "ended",
        })
      );
    }
  }

  return { nodes, edges };
};
