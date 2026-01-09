/**
 * AG_Cohub Pattern Types
 *
 * Type definitions for the modular pattern system.
 * These types bridge AG_Cohub JSON patterns with the AutoGen Studio frontend.
 */

// ============================================
// JSON PATTERN FORMAT (AG_Cohub/patterns/*.json)
// ============================================

export interface CoHubPatternJSON {
  id: string;
  name: {
    en: string;
    ko: string;
  };
  description: {
    en: string;
    ko: string;
  };
  diagram: string;
  complexity: "low" | "medium" | "high" | "very-high";
  when_to_use: string[];
  when_to_avoid: string[];
  pros: string[];
  cons: string[];
  example_use_cases: Array<{
    name: string;
    [key: string]: unknown;
  }>;
  autogen_implementation: {
    provider: string;
    label?: string;
    team_config?: {
      participants: Array<{
        provider: string;
        component_type: string;
        config: {
          name: string;
          description: string;
          system_message: string;
          handoffs?: string[];
        };
      }>;
      selector_prompt?: string;
    };
  };
  best_practices?: string[];  // optional - 일부 패턴에 없을 수 있음
  references: Array<{
    title: string;
    url: string;
  }>;

  /**
   * 시각화 커스터마이징 (선택적)
   * providers.json 기본값을 오버라이드
   */
  visual_override?: {
    layout?: LayoutType;
    category?: PatternCategory;
    icon?: string;
    primaryColor?: string;
    secondaryColor?: string;
    centerNodeType?: "selector" | "supervisor" | "aggregator" | "triage";
    edgeStyle?: "solid" | "dashed" | "animated";
    bidirectional?: boolean;
    showCrossConnections?: boolean;
  };
}

// ============================================
// FRONTEND PATTERN FORMAT (PatternDefinition)
// ============================================

export type PatternCategory =
  | "sequential"
  | "dynamic"
  | "parallel"
  | "hierarchical";

export type LayoutType =
  | "chain"
  | "hub-spoke"
  | "mesh"
  | "tree"
  | "fork-join"
  | "ring";

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

  // Extended fields from CoHub
  complexity?: string;
  pros?: string[];
  cons?: string[];
  bestPractices?: string[];
  references?: Array<{ title: string; url: string }>;
}

// ============================================
// TEAM CONFIG FORMAT (AutoGen Runtime)
// ============================================

export interface AgentConfig {
  name: string;
  description?: string;
  system_message?: string;
  model_client?: ModelClientConfig;
  handoffs?: string[];
}

export interface ModelClientConfig {
  provider: string;
  component_type: "model";
  config: Record<string, unknown>;
}

export interface TerminationConfig {
  provider: string;
  component_type: "termination";
  config: Record<string, unknown>;
}

export interface TeamConfig {
  participants: Array<{
    provider: string;
    component_type: "agent";
    config: AgentConfig;
  }>;
  model_client?: ModelClientConfig;
  selector_prompt?: string;
  allow_repeated_speaker?: boolean;
  termination_condition?: TerminationConfig;
}

export interface Component<T> {
  provider: string;
  component_type: string;
  config: T;
}
