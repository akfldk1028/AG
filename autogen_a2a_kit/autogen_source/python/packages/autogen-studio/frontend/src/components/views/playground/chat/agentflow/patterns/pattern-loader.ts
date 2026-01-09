/**
 * Pattern Loader - JSON 기반 패턴 로딩 시스템
 *
 * AG_Cohub/patterns/*.json에서 패턴을 로드하고 PatternDefinition으로 변환
 *
 * ## 사용법
 * patterns/data/ 폴더에 JSON 추가 → 자동 로드
 *
 * ## 새 패턴 추가 시
 * 1. AG_Cohub/patterns/에 JSON 추가
 * 2. 이 폴더(data/)에 복사
 * 3. 아래 PATTERN_JSON_FILES에 import 추가
 */

import { PatternDefinition, PatternCategory, LayoutType, PatternVisual, PatternConnection } from "./pattern-types";

// ============================================
// JSON 타입 정의 (AG_Cohub/loader/types.ts 기반)
// ============================================

interface CoHubPatternJSON {
  id: string;
  name: { en: string; ko: string };
  description: { en: string; ko: string };
  diagram: string;
  complexity: "low" | "medium" | "high" | "very-high";
  when_to_use: string[];
  when_to_avoid: string[];
  pros: string[];
  cons: string[];
  example_use_cases: Array<{ name: string; [key: string]: unknown }>;
  autogen_implementation: {
    provider: string;
    label?: string;
    requiredConfig?: {
      allow_repeated_speaker?: boolean;
      model_client?: {
        provider: string;
        config: Record<string, unknown>;
      };
    };
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
  best_practices?: string[];
  references: Array<{ title: string; url: string }>;
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

interface ProviderConfig {
  full: string;
  category: PatternCategory;
  layout: LayoutType;
  icon: string;
  colors: { primary: string; secondary: string };
  communicationStyle: "turn-based" | "broadcast" | "request-response" | "event-driven";
  connections: PatternConnection[];
  requiresModelClient: boolean;
}

// ============================================
// Provider 설정 로드
// ============================================

import providersJson from "./data/providers.json";

const { _README, ...providers } = providersJson as any;
const PROVIDERS: Record<string, ProviderConfig> = providers;

function extractProviderShort(provider: string): string {
  const parts = provider.split(".");
  return parts[parts.length - 1];
}

function getProvider(providerFull: string): ProviderConfig | undefined {
  const shortName = extractProviderShort(providerFull);
  return PROVIDERS[shortName];
}

// ============================================
// 패턴 JSON 로드
// ============================================

import sequential from "./data/01_sequential.json";
import concurrent from "./data/02_concurrent.json";
import selector from "./data/03_selector.json";
import groupChat from "./data/04_group_chat.json";
import handoff from "./data/05_handoff.json";
import magentic from "./data/06_magentic.json";
import debate from "./data/07_debate.json";
import reflection from "./data/08_reflection.json";
import hierarchical from "./data/09_hierarchical.json";

const PATTERN_JSON_FILES: CoHubPatternJSON[] = [
  sequential as CoHubPatternJSON,
  concurrent as CoHubPatternJSON,
  selector as CoHubPatternJSON,
  groupChat as CoHubPatternJSON,
  handoff as CoHubPatternJSON,
  magentic as CoHubPatternJSON,
  debate as CoHubPatternJSON,
  reflection as CoHubPatternJSON,
  hierarchical as CoHubPatternJSON,
];

// ============================================
// JSON → PatternDefinition 변환
// ============================================

function convertToPatternDefinition(json: CoHubPatternJSON): PatternDefinition {
  const providerFull = json.autogen_implementation.provider;
  const providerShort = extractProviderShort(providerFull);
  const providerConfig = getProvider(providerFull);

  // 기본값
  const baseCategory = providerConfig?.category || "sequential";
  const baseLayout = providerConfig?.layout || "chain";
  const baseIcon = providerConfig?.icon || "ArrowRight";
  const baseColors = providerConfig?.colors || { primary: "#3b82f6", secondary: "#93c5fd" };
  const baseCommunicationStyle = providerConfig?.communicationStyle || "turn-based";
  const baseConnections = providerConfig?.connections || [{ type: "sequential" as const, from: "agent[i]", to: "agent[i+1]" }];
  const requiresModelClient = providerConfig?.requiresModelClient ?? false;

  // JSON의 visual_override 확인
  const override = json.visual_override || {};

  // Visual 설정
  const visual: PatternVisual = {
    layout: override.layout || baseLayout,
    centerNodeType: override.centerNodeType,
    edgeStyle: override.edgeStyle || "solid",
    bidirectional: override.bidirectional ?? false,
    showCrossConnections: override.showCrossConnections ?? false,
    primaryColor: override.primaryColor || baseColors.primary,
    secondaryColor: override.secondaryColor || baseColors.secondary,
    icon: override.icon || baseIcon,
  };

  // Coordinator 역할 매핑
  const coordinatorRoles: Record<string, string> = {
    SelectorGroupChat: "LLM Selector",
    Swarm: "Triage Agent",
    MagenticOneGroupChat: "Orchestrator",
  };

  // 최소 에이전트 수
  const participants = json.autogen_implementation.team_config?.participants;
  const minAgents = participants ? Math.max(2, participants.length) : 2;

  // 에이전트 역할
  const agentRoles = participants?.map((p) => p.config.name) || [];

  return {
    id: json.id,
    name: json.name.en,
    category: override.category || baseCategory,
    description: json.description.en,
    useCases: json.when_to_use.slice(0, 3),

    structure: {
      requiresCoordinator: requiresModelClient || providerShort === "Swarm",
      coordinatorRole: coordinatorRoles[providerShort],
      minAgents,
      maxAgents: undefined,
      agentRoles,
    },

    communication: {
      style: baseCommunicationStyle,
      connections: baseConnections,
    },

    visual,

    autogenProvider: providerShort,
    autogenProviderFull: providerFull,

    requiredConfig: getRequiredConfig(providerShort, json),
    prompts: getPrompts(json),
  };
}

function getRequiredConfig(provider: string, json: CoHubPatternJSON): PatternDefinition["requiredConfig"] {
  if (provider === "SelectorGroupChat" || provider === "MagenticOneGroupChat") {
    // Read from JSON's requiredConfig if available
    const jsonRequiredConfig = json.autogen_implementation?.requiredConfig;

    // Defaults
    const defaults = {
      model_client: {
        provider: "autogen_ext.models.openai.OpenAIChatCompletionClient",
        config: { model: "gpt-4o-mini" },
      },
      allow_repeated_speaker: true, // Default true, but can be overridden by JSON
    };

    // Merge JSON config over defaults (JSON values take precedence)
    return {
      ...defaults,
      ...jsonRequiredConfig,
    };
  }
  return undefined;
}

function getPrompts(json: CoHubPatternJSON): PatternDefinition["prompts"] {
  const selectorPrompt = json.autogen_implementation.team_config?.selector_prompt;
  return selectorPrompt ? { selector: selectorPrompt } : undefined;
}

// ============================================
// PATTERN_LIBRARY 생성 (동적!)
// ============================================

export const LOADED_PATTERN_LIBRARY: PatternDefinition[] = PATTERN_JSON_FILES
  .map(convertToPatternDefinition)
  .sort((a, b) => a.id.localeCompare(b.id));

// ============================================
// 헬퍼 함수
// ============================================

export const getLoadedPatternById = (id: string): PatternDefinition | undefined => {
  return LOADED_PATTERN_LIBRARY.find((p) => p.id === id);
};

export const getLoadedPatternsByCategory = (category: PatternCategory): PatternDefinition[] => {
  return LOADED_PATTERN_LIBRARY.filter((p) => p.category === category);
};

// ============================================
// TeamConfig 템플릿 생성 (동적!)
// ============================================

import { Component, TeamConfig, AgentConfig } from "../../../../../types/datamodel";

/**
 * Default model client - used for all agents
 */
export const DEFAULT_MODEL_CLIENT = {
  provider: "autogen_ext.models.openai.OpenAIChatCompletionClient",
  component_type: "model" as const,
  config: {
    model: "gpt-4o-mini",
    temperature: 0.7,
  },
};

/**
 * Default termination condition
 */
export const DEFAULT_TERMINATION = {
  provider: "autogen_agentchat.conditions.TextMentionTermination",
  component_type: "termination" as const,
  config: {
    text: "TERMINATE",
  },
};

/**
 * JSON에서 TeamConfig 템플릿 생성
 */
function buildTeamTemplate(json: CoHubPatternJSON): Component<TeamConfig> {
  const providerFull = json.autogen_implementation.provider;
  const providerShort = extractProviderShort(providerFull);
  const teamConfig = json.autogen_implementation.team_config;

  // 참가자 생성
  const participants: Component<AgentConfig>[] = teamConfig?.participants?.map((p) => ({
    provider: p.provider,
    component_type: "agent" as const,
    config: {
      name: p.config.name,
      description: p.config.description,
      system_message: p.config.system_message,
      model_client: DEFAULT_MODEL_CLIENT,
      ...(p.config.handoffs ? { handoffs: p.config.handoffs } : {}),
    } as AgentConfig,
  })) || [
    // 기본 참가자 (JSON에 없는 경우)
    {
      provider: "autogen_agentchat.agents.AssistantAgent",
      component_type: "agent" as const,
      config: {
        name: "Agent_1",
        description: "First agent",
        system_message: "You are a helpful assistant.",
        model_client: DEFAULT_MODEL_CLIENT,
      } as AgentConfig,
    },
    {
      provider: "autogen_agentchat.agents.AssistantAgent",
      component_type: "agent" as const,
      config: {
        name: "Agent_2",
        description: "Second agent",
        system_message: "You are a helpful assistant. Say TERMINATE when done.",
        model_client: DEFAULT_MODEL_CLIENT,
      } as AgentConfig,
    },
  ];

  // 기본 config
  const config: any = {
    participants,
    termination_condition: DEFAULT_TERMINATION,
  };

  // SelectorGroupChat/MagenticOneGroupChat는 model_client 필요
  if (providerShort === "SelectorGroupChat" || providerShort === "MagenticOneGroupChat") {
    config.model_client = DEFAULT_MODEL_CLIENT;
    config.allow_repeated_speaker = true;
  }

  // selector_prompt 추가
  if (teamConfig?.selector_prompt) {
    config.selector_prompt = teamConfig.selector_prompt;
  }

  return {
    provider: providerFull,
    component_type: "team",
    config: config as TeamConfig,
  };
}

/**
 * 모든 패턴의 TeamConfig 템플릿
 */
export const LOADED_PATTERN_TEMPLATES: Record<string, Component<TeamConfig>> = {};

// 동적으로 템플릿 생성
PATTERN_JSON_FILES.forEach((json) => {
  LOADED_PATTERN_TEMPLATES[json.id] = buildTeamTemplate(json);
});

/**
 * ID로 템플릿 조회
 */
export const getLoadedPatternTemplate = (id: string): Component<TeamConfig> | undefined => {
  return LOADED_PATTERN_TEMPLATES[id];
};

export default {
  LOADED_PATTERN_LIBRARY,
  LOADED_PATTERN_TEMPLATES,
  getLoadedPatternById,
  getLoadedPatternsByCategory,
  getLoadedPatternTemplate,
  DEFAULT_MODEL_CLIENT,
  DEFAULT_TERMINATION,
};
