/**
 * Layout Generator
 *
 * Generates React Flow layouts based on abstract pattern definitions.
 * Each layout type has distinct visual characteristics.
 */

import { Node } from "@xyflow/react";
import { CustomEdge } from "../edge";
import {
  PatternDefinition,
  LayoutType,
  PatternVisual,
} from "./pattern-schema";
import {
  Component,
  AgentConfig,
  TeamConfig,
  Run,
} from "../../../../../types/datamodel";
import {
  PatternLayoutResult,
  NODE_DIMENSIONS,
  createAgentNode,
  createUserNode,
  createEndNode,
  createEdge,
} from "./types";

// Layout constants - increased spacing for better visibility
const CANVAS = {
  centerX: 450,
  centerY: 280,
  radius: 280,
  layerSpacing: 180,
  nodeSpacing: 240,
};

/**
 * Create a special hub/coordinator node
 */
const createHubNode = (
  id: string,
  name: string,
  type: "selector" | "supervisor" | "aggregator" | "triage",
  visual: PatternVisual,
  position: { x: number; y: number },
  isActive: boolean,
  isProcessing: boolean
): Node => {
  const typeLabels = {
    selector: { label: "LLM Selector", icon: "🎯" },
    supervisor: { label: "Supervisor", icon: "👔" },
    aggregator: { label: "Aggregator", icon: "📊" },
    triage: { label: "Triage", icon: "🔀" },
  };

  const typeInfo = typeLabels[type];

  return {
    id,
    type: "agentNode",
    position,
    data: {
      label: name || typeInfo.label,
      agentType: typeInfo.label,
      description: `${typeInfo.icon} ${typeInfo.label}`,
      isActive,
      isProcessing,
      isHub: true,
      hubType: type,
      color: visual.primaryColor,
    },
  };
};

/**
 * Generate CHAIN layout (Sequential)
 * A → B → C → D
 */
const generateChainLayout = (
  participants: Component<AgentConfig>[],
  visual: PatternVisual,
  participatedAgents: Set<string>,
  isProcessing: boolean,
  isComplete: boolean,
  run?: Run
): PatternLayoutResult => {
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];

  const startX = 50;
  const y = CANVAS.centerY - NODE_DIMENSIONS.default.height / 2;

  // User node
  nodes.push(
    createUserNode(
      { x: startX, y },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // Agent nodes in a line
  participants.forEach((p, index) => {
    const agentName = p.config?.name || `agent-${index}`;
    const x = startX + (index + 1) * CANVAS.nodeSpacing;

    nodes.push(
      createAgentNode(
        agentName,
        agentName,
        p.label || "",
        p.description || "",
        { x, y },
        participatedAgents.has(agentName),
        isProcessing
      )
    );

    // Edge from previous
    const prevId = index === 0 ? "user" : participants[index - 1].config?.name || `agent-${index - 1}`;
    const isActive = participatedAgents.has(agentName);

    edges.push(
      createEdge(`${prevId}-to-${agentName}`, prevId, agentName, {
        stroke: isActive ? visual.primaryColor : "#6b7280",
        strokeWidth: isActive ? 2 : 1,
        animated: isActive && isProcessing,
      })
    );

    // Loop back edge for reflection pattern
    if (visual.bidirectional && index === participants.length - 1 && participants.length === 2) {
      edges.push(
        createEdge(`${agentName}-loop`, agentName, participants[0].config?.name || "agent-0", {
          stroke: visual.secondaryColor,
          strokeWidth: 1,
          strokeDasharray: "5,5",
          label: "revise",
          routingType: "secondary",  // Loop uses secondary routing style
        })
      );
    }
  });

  // End node
  if (isComplete) {
    const lastAgent = participants[participants.length - 1];
    const lastAgentName = lastAgent?.config?.name || `agent-${participants.length - 1}`;
    const endX = startX + (participants.length + 1) * CANVAS.nodeSpacing;

    nodes.push(createEndNode({ x: endX, y }, run));
    edges.push(
      createEdge(`${lastAgentName}-to-end`, lastAgentName, "end", {
        stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
        strokeWidth: 2,
      })
    );
  }

  return { nodes, edges };
};

/**
 * Generate HUB-SPOKE layout (Selector, Supervisor)
 * Central hub with agents arranged in semi-circle
 */
const generateHubSpokeLayout = (
  participants: Component<AgentConfig>[],
  visual: PatternVisual,
  participatedAgents: Set<string>,
  isProcessing: boolean,
  isComplete: boolean,
  run?: Run
): PatternLayoutResult => {
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];

  // User node
  nodes.push(
    createUserNode(
      {
        x: CANVAS.centerX - 300,
        y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2,
      },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // Central hub node
  const hubId = visual.centerNodeType || "hub";
  nodes.push(
    createHubNode(
      hubId,
      "",
      visual.centerNodeType || "selector",
      visual,
      {
        x: CANVAS.centerX - NODE_DIMENSIONS.default.width / 2,
        y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2,
      },
      true,
      isProcessing
    )
  );

  // Edge from user to hub
  edges.push(
    createEdge("user-to-hub", "user", hubId, {
      stroke: "#2563eb",
      strokeWidth: 2,
      animated: participatedAgents.size > 0,
    })
  );

  // Agents in semi-circle
  const startAngle = -Math.PI / 2.5; // Wider spread
  const endAngle = Math.PI / 2.5;
  const angleStep = participants.length > 1
    ? (endAngle - startAngle) / (participants.length - 1)
    : 0;

  participants.forEach((p, index) => {
    const agentName = p.config?.name || `agent-${index}`;
    const angle = participants.length === 1 ? 0 : startAngle + index * angleStep;
    const x = CANVAS.centerX + CANVAS.radius * Math.cos(angle);
    const y = CANVAS.centerY + CANVAS.radius * Math.sin(angle);

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

    // Hub to agent edge
    edges.push(
      createEdge(`hub-to-${agentName}`, hubId, agentName, {
        animated: isAgentActive && isProcessing,
        stroke: isAgentActive ? visual.primaryColor : "#6b7280",
        strokeWidth: isAgentActive ? 2 : 1,
        opacity: isAgentActive ? 1 : 0.4,
        label: isAgentActive && visual.centerNodeType === "selector" ? "selected" : "",
      })
    );

    // Return edge (if bidirectional)
    if (visual.bidirectional) {
      edges.push(
        createEdge(`${agentName}-to-hub`, agentName, hubId, {
          stroke: isAgentActive ? visual.secondaryColor : "#6b7280",
          strokeWidth: 1,
          strokeDasharray: "5,5",
          opacity: isAgentActive ? 0.7 : 0.2,
          routingType: "secondary",
        })
      );
    }
  });

  // End node
  if (isComplete) {
    nodes.push(
      createEndNode(
        {
          x: CANVAS.centerX + CANVAS.radius + 100,
          y: CANVAS.centerY - NODE_DIMENSIONS.end.height / 2,
        },
        run
      )
    );

    edges.push(
      createEdge("hub-to-end", hubId, "end", {
        stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
        strokeWidth: 2,
      })
    );
  }

  return { nodes, edges };
};

/**
 * Generate MESH layout (Swarm)
 * All agents can communicate with each other
 */
const generateMeshLayout = (
  participants: Component<AgentConfig>[],
  visual: PatternVisual,
  participatedAgents: Set<string>,
  isProcessing: boolean,
  isComplete: boolean,
  run?: Run
): PatternLayoutResult => {
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];

  // User node
  nodes.push(
    createUserNode(
      {
        x: CANVAS.centerX - 350,
        y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2,
      },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // First agent as triage (center)
  const triageAgent = participants[0];
  const triageName = triageAgent?.config?.name || "triage";
  const otherAgents = participants.slice(1);

  nodes.push(
    createHubNode(
      triageName,
      triageName,
      "triage",
      visual,
      {
        x: CANVAS.centerX - NODE_DIMENSIONS.default.width / 2,
        y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2,
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

  // Other agents in circle around triage
  const angleStep = (2 * Math.PI) / Math.max(1, otherAgents.length);
  const startAngle = -Math.PI / 2;

  otherAgents.forEach((p, index) => {
    const agentName = p.config?.name || `agent-${index + 1}`;
    const angle = startAngle + index * angleStep;
    const x = CANVAS.centerX + CANVAS.radius * Math.cos(angle);
    const y = CANVAS.centerY + CANVAS.radius * Math.sin(angle);

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

    // Bidirectional edges with triage
    edges.push(
      createEdge(`${triageName}-to-${agentName}`, triageName, agentName, {
        animated: isAgentActive && isProcessing,
        stroke: isAgentActive ? visual.primaryColor : "#6b7280",
        strokeWidth: isAgentActive ? 2 : 1,
        strokeDasharray: visual.edgeStyle === "dashed" ? "8,4" : undefined,
        opacity: isAgentActive ? 1 : 0.4,
        label: isAgentActive ? "handoff" : "",
      })
    );

    edges.push(
      createEdge(`${agentName}-to-${triageName}`, agentName, triageName, {
        stroke: isAgentActive ? visual.secondaryColor : "#6b7280",
        strokeWidth: 1,
        strokeDasharray: "5,5",
        opacity: isAgentActive ? 0.8 : 0.2,
        routingType: "secondary",
      })
    );
  });

  // Cross-agent connections (mesh)
  if (visual.showCrossConnections && otherAgents.length > 1) {
    otherAgents.forEach((p1, i) => {
      otherAgents.forEach((p2, j) => {
        if (i < j) { // Only one direction to avoid duplicates
          const agent1 = p1.config?.name || `agent-${i + 1}`;
          const agent2 = p2.config?.name || `agent-${j + 1}`;
          const bothActive = participatedAgents.has(agent1) && participatedAgents.has(agent2);

          if (bothActive) {
            edges.push(
              createEdge(`${agent1}-mesh-${agent2}`, agent1, agent2, {
                stroke: "#a855f7", // Purple for mesh
                strokeWidth: 1,
                strokeDasharray: "3,3",
                opacity: 0.5,
                label: "↔",
              })
            );
          }
        }
      });
    });
  }

  // End node
  if (isComplete) {
    nodes.push(
      createEndNode(
        {
          x: CANVAS.centerX + CANVAS.radius + 100,
          y: CANVAS.centerY - NODE_DIMENSIONS.end.height / 2,
        },
        run
      )
    );

    const lastActive = [...participatedAgents].filter(a => a !== "user").pop();
    if (lastActive) {
      edges.push(
        createEdge(`${lastActive}-to-end`, lastActive, "end", {
          stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
          strokeWidth: 2,
        })
      );
    }
  }

  return { nodes, edges };
};

/**
 * Generate FORK-JOIN layout (Parallel)
 * User → Aggregator → [Agent1, Agent2, ...] → Aggregator → End
 */
const generateForkJoinLayout = (
  participants: Component<AgentConfig>[],
  visual: PatternVisual,
  participatedAgents: Set<string>,
  isProcessing: boolean,
  isComplete: boolean,
  run?: Run
): PatternLayoutResult => {
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];

  const leftX = 50;
  const centerX = CANVAS.centerX;
  const rightX = CANVAS.centerX + CANVAS.radius + 50;

  // User node
  nodes.push(
    createUserNode(
      { x: leftX, y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2 },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // Aggregator node (left - distributes)
  nodes.push(
    createHubNode(
      "aggregator-in",
      "Distribute",
      "aggregator",
      visual,
      {
        x: leftX + 180,
        y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2,
      },
      true,
      isProcessing
    )
  );

  edges.push(
    createEdge("user-to-agg", "user", "aggregator-in", {
      stroke: "#2563eb",
      strokeWidth: 2,
      animated: isProcessing,
    })
  );

  // Worker agents (spread vertically)
  const agentSpacing = 140;
  const startY = CANVAS.centerY - ((participants.length - 1) * agentSpacing) / 2;

  participants.forEach((p, index) => {
    const agentName = p.config?.name || `agent-${index}`;
    const y = startY + index * agentSpacing;

    nodes.push(
      createAgentNode(
        agentName,
        agentName,
        p.label || "",
        p.description || "",
        { x: centerX, y: y - NODE_DIMENSIONS.default.height / 2 },
        participatedAgents.has(agentName),
        isProcessing
      )
    );

    const isActive = participatedAgents.has(agentName);

    // Fan-out edges
    edges.push(
      createEdge(`agg-to-${agentName}`, "aggregator-in", agentName, {
        stroke: isActive ? visual.primaryColor : "#6b7280",
        strokeWidth: isActive ? 2 : 1,
        animated: isActive && isProcessing,
        label: isActive ? "task" : "",
      })
    );

    // Fan-in edges
    edges.push(
      createEdge(`${agentName}-to-agg-out`, agentName, "aggregator-out", {
        stroke: isActive ? visual.secondaryColor : "#6b7280",
        strokeWidth: isActive ? 2 : 1,
        animated: isActive && isProcessing,
        label: isActive ? "result" : "",
      })
    );
  });

  // Aggregator node (right - collects)
  nodes.push(
    createHubNode(
      "aggregator-out",
      "Aggregate",
      "aggregator",
      visual,
      {
        x: rightX,
        y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2,
      },
      participatedAgents.size > 1,
      isProcessing
    )
  );

  // End node
  if (isComplete) {
    nodes.push(
      createEndNode(
        { x: rightX + 180, y: CANVAS.centerY - NODE_DIMENSIONS.end.height / 2 },
        run
      )
    );

    edges.push(
      createEdge("agg-out-to-end", "aggregator-out", "end", {
        stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
        strokeWidth: 2,
      })
    );
  }

  return { nodes, edges };
};

/**
 * Generate TREE layout (Hierarchical)
 * Leader → Planners → Workers
 */
const generateTreeLayout = (
  participants: Component<AgentConfig>[],
  visual: PatternVisual,
  participatedAgents: Set<string>,
  isProcessing: boolean,
  isComplete: boolean,
  run?: Run
): PatternLayoutResult => {
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];

  // Simple 2-level tree for now
  // First agent is leader, rest are workers
  const leader = participants[0];
  const leaderName = leader?.config?.name || "leader";
  const workers = participants.slice(1);

  // User node
  nodes.push(
    createUserNode(
      { x: 50, y: 50 },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // Leader node
  nodes.push(
    createHubNode(
      leaderName,
      leaderName,
      "supervisor",
      visual,
      { x: 250, y: 50 },
      participatedAgents.has(leaderName),
      isProcessing
    )
  );

  edges.push(
    createEdge("user-to-leader", "user", leaderName, {
      stroke: "#2563eb",
      strokeWidth: 2,
      animated: participatedAgents.has(leaderName),
    })
  );

  // Worker nodes
  const workerY = 320;
  const workerSpacing = 250;
  const startX = CANVAS.centerX - ((workers.length - 1) * workerSpacing) / 2;

  workers.forEach((p, index) => {
    const agentName = p.config?.name || `worker-${index}`;
    const x = startX + index * workerSpacing;

    nodes.push(
      createAgentNode(
        agentName,
        agentName,
        p.label || "",
        p.description || "",
        { x, y: workerY },
        participatedAgents.has(agentName),
        isProcessing
      )
    );

    const isActive = participatedAgents.has(agentName);

    // Leader to worker
    edges.push(
      createEdge(`${leaderName}-to-${agentName}`, leaderName, agentName, {
        stroke: isActive ? visual.primaryColor : "#6b7280",
        strokeWidth: isActive ? 2 : 1,
        animated: isActive && isProcessing,
      })
    );

    // Worker back to leader
    if (visual.bidirectional) {
      edges.push(
        createEdge(`${agentName}-to-${leaderName}`, agentName, leaderName, {
          stroke: isActive ? visual.secondaryColor : "#6b7280",
          strokeWidth: 1,
          strokeDasharray: "5,5",
          opacity: isActive ? 0.7 : 0.3,
          routingType: "secondary",
        })
      );
    }
  });

  // End node
  if (isComplete) {
    nodes.push(
      createEndNode(
        { x: 500, y: 50 },
        run
      )
    );

    edges.push(
      createEdge("leader-to-end", leaderName, "end", {
        stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
        strokeWidth: 2,
      })
    );
  }

  return { nodes, edges };
};

/**
 * Generate RING layout (Debate)
 * Circular arrangement with all-to-all connections
 */
const generateRingLayout = (
  participants: Component<AgentConfig>[],
  visual: PatternVisual,
  participatedAgents: Set<string>,
  isProcessing: boolean,
  isComplete: boolean,
  run?: Run
): PatternLayoutResult => {
  const nodes: Node[] = [];
  const edges: CustomEdge[] = [];

  // User node
  nodes.push(
    createUserNode(
      { x: CANVAS.centerX - 350, y: CANVAS.centerY - NODE_DIMENSIONS.default.height / 2 },
      participatedAgents.has("user"),
      isProcessing
    )
  );

  // Agents in a circle
  const angleStep = (2 * Math.PI) / participants.length;
  const startAngle = -Math.PI / 2;

  participants.forEach((p, index) => {
    const agentName = p.config?.name || `agent-${index}`;
    const angle = startAngle + index * angleStep;
    const x = CANVAS.centerX + (CANVAS.radius * 0.8) * Math.cos(angle);
    const y = CANVAS.centerY + (CANVAS.radius * 0.8) * Math.sin(angle);

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
  });

  // First agent connects to user
  const firstAgent = participants[0]?.config?.name || "agent-0";
  edges.push(
    createEdge("user-to-first", "user", firstAgent, {
      stroke: "#2563eb",
      strokeWidth: 2,
      animated: participatedAgents.has(firstAgent),
    })
  );

  // All-to-all connections in ring
  if (visual.showCrossConnections) {
    participants.forEach((p1, i) => {
      participants.forEach((p2, j) => {
        if (i < j) {
          const agent1 = p1.config?.name || `agent-${i}`;
          const agent2 = p2.config?.name || `agent-${j}`;
          const bothActive = participatedAgents.has(agent1) && participatedAgents.has(agent2);

          edges.push(
            createEdge(`${agent1}-debate-${agent2}`, agent1, agent2, {
              stroke: bothActive ? visual.primaryColor : "#6b7280",
              strokeWidth: bothActive ? 2 : 1,
              strokeDasharray: "4,4",
              opacity: bothActive ? 0.8 : 0.3,
              label: bothActive ? "💬" : "",
            })
          );
        }
      });
    });
  }

  // End node
  if (isComplete) {
    nodes.push(
      createEndNode(
        { x: CANVAS.centerX + CANVAS.radius + 100, y: CANVAS.centerY - NODE_DIMENSIONS.end.height / 2 },
        run
      )
    );

    const lastActive = [...participatedAgents].filter(a => a !== "user").pop();
    if (lastActive) {
      edges.push(
        createEdge(`${lastActive}-to-end`, lastActive, "end", {
          stroke: run?.status === "complete" ? "#22c55e" : "#ef4444",
          strokeWidth: 2,
          label: "verdict",
        })
      );
    }
  }

  return { nodes, edges };
};

/**
 * Main layout generator - routes to appropriate generator based on layout type
 */
export const generateLayoutFromPattern = (
  pattern: PatternDefinition,
  teamConfig: Component<TeamConfig>,
  participatedAgents: Set<string>,
  run?: Run
): PatternLayoutResult => {
  const participants = teamConfig.config?.participants || [];
  const isProcessing = run?.status === "active" || run?.status === "awaiting_input";
  const isComplete = ["complete", "error", "stopped"].includes(run?.status || "");

  const layoutGenerators: Record<LayoutType, () => PatternLayoutResult> = {
    chain: () => generateChainLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run),
    "hub-spoke": () => generateHubSpokeLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run),
    mesh: () => generateMeshLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run),
    "fork-join": () => generateForkJoinLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run),
    tree: () => generateTreeLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run),
    ring: () => generateRingLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run),
  };

  const generator = layoutGenerators[pattern.visual.layout];
  return generator ? generator() : generateChainLayout(participants, pattern.visual, participatedAgents, isProcessing, isComplete, run);
};
