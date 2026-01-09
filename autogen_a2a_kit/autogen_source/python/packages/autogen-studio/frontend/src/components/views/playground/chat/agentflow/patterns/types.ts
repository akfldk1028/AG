import { Node } from "@xyflow/react";
import {
  Component,
  AgentConfig,
  TeamConfig,
  Run,
} from "../../../../../types/datamodel";
import { CustomEdge } from "../edge";

// Pattern types
export type PatternType =
  | "sequential"
  | "selector"
  | "handoff"
  | "debate"
  | "reflection"
  | "unknown";

// Pattern layout result
export interface PatternLayoutResult {
  nodes: Node[];
  edges: CustomEdge[];
}

// Pattern generator function signature
export interface PatternGenerator {
  (
    teamConfig: Component<TeamConfig>,
    participatedAgents: Set<string>,
    run?: Run
  ): PatternLayoutResult;
}

// Node dimensions
export const NODE_DIMENSIONS = {
  default: { width: 170, height: 100 },
  end: { width: 170, height: 80 },
  task: { width: 170, height: 100 },
};

// Common node creator
export const createAgentNode = (
  id: string,
  label: string,
  agentType: string,
  description: string,
  position: { x: number; y: number },
  isActive: boolean,
  isProcessing: boolean
): Node => ({
  id,
  type: "agentNode",
  position,
  data: {
    type: "agent",
    label,
    agentType,
    description,
    isActive,
    status: "",
    reason: "",
    draggable: !isProcessing,
  },
});

// Create user node
export const createUserNode = (
  position: { x: number; y: number },
  isActive: boolean,
  isProcessing: boolean
): Node => ({
  id: "user",
  type: "agentNode",
  position,
  data: {
    type: "user",
    label: "User",
    agentType: "user",
    description: "Human user",
    isActive,
    status: "",
    reason: "",
    draggable: !isProcessing,
  },
});

// Create end node
export const createEndNode = (
  position: { x: number; y: number },
  run?: Run
): Node => ({
  id: "end",
  type: "agentNode",
  position,
  data: {
    type: "end",
    label: "End",
    status: run?.status,
    reason: run?.error_message || "",
    agentType: "",
    description: "",
    isActive: false,
    draggable: false,
  },
});

// Create a basic edge
export const createEdge = (
  id: string,
  source: string,
  target: string,
  options: {
    animated?: boolean;
    stroke?: string;
    strokeWidth?: number;
    strokeDasharray?: string;
    opacity?: number;
    label?: string;
    routingType?: "primary" | "secondary";
  } = {}
): CustomEdge => ({
  id,
  source,
  target,
  type: "custom",
  animated: options.animated || false,
  data: {
    label: options.label || "",
    messages: [],
    routingType: options.routingType,
  },
  style: {
    stroke: options.stroke || "#2563eb",
    strokeWidth: options.strokeWidth || 1,
    strokeDasharray: options.strokeDasharray,
    opacity: options.opacity || 1,
  },
});
