/**
 * Pattern Type Definitions
 *
 * Shared types for pattern system.
 * Extracted to avoid circular dependencies between pattern-schema.ts and pattern-loader.ts
 */

export type PatternCategory =
  | "sequential"    // Fixed order execution
  | "dynamic"       // Runtime agent selection
  | "parallel"      // Concurrent execution
  | "hierarchical"; // Multi-level coordination

export type LayoutType =
  | "chain"        // Linear: A → B → C
  | "hub-spoke"    // Central hub + radial agents
  | "mesh"         // Full interconnection
  | "tree"         // Hierarchical layers
  | "fork-join"    // Fan-out then merge
  | "ring";        // Circular with voting

export interface PatternVisual {
  layout: LayoutType;
  centerNodeType?: "selector" | "supervisor" | "aggregator" | "triage";
  edgeStyle: "solid" | "dashed" | "animated";
  bidirectional: boolean;
  showCrossConnections: boolean;
  primaryColor: string;
  secondaryColor: string;
  icon: string;
}

export interface PatternConnection {
  type: "sequential" | "broadcast" | "selective" | "handoff" | "return";
  from: string | string[];
  to: string | string[];
  condition?: string;
}

export interface PatternDefinition {
  id: string;
  name: string;
  category: PatternCategory;
  description: string;
  useCases: string[];

  structure: {
    requiresCoordinator: boolean;
    coordinatorRole?: string;
    minAgents: number;
    maxAgents?: number;
    agentRoles?: string[];
  };

  communication: {
    style: "turn-based" | "broadcast" | "request-response" | "event-driven";
    connections: PatternConnection[];
  };

  visual: PatternVisual;

  autogenProvider: string;
  autogenProviderFull: string;

  requiredConfig?: {
    model_client?: {
      provider: string;
      config: Record<string, unknown>;
    };
    allow_repeated_speaker?: boolean;
  };

  prompts?: {
    selector?: string;
    termination?: string;
    system?: string;
  };

  // Extended fields from CoHub JSON
  complexity?: string;
  pros?: string[];
  cons?: string[];
  bestPractices?: string[];
  references?: Array<{ title: string; url: string }>;
}
