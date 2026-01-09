/**
 * ============================================
 * CONVERTER - JSON을 Frontend/Runtime 형식으로 변환
 * ============================================
 *
 * 이 파일 하나가 모든 변환 로직을 담당:
 * - convertToPatternDefinition(): JSON → UI용 PatternDefinition
 * - buildTeamTemplate(): JSON → Runtime용 TeamConfig
 *
 * !! 이 파일은 수정할 필요 없음 !!
 * - 새 패턴 추가: patterns/*.json
 * - 새 provider 추가: providers.json
 */

import {
  CoHubPatternJSON,
  PatternDefinition,
  PatternVisual,
  Component,
  TeamConfig,
  AgentConfig,
  ModelClientConfig,
  TerminationConfig,
} from "./types";

import {
  extractProviderShort,
  getCategory,
  getLayout,
  getIcon,
  getColors,
  getCommunicationStyle,
  getConnections,
  requiresModelClient,
  getDefaultParticipants,
} from "./providers";

// ============================================
// 기본 설정값
// ============================================

export const DEFAULT_MODEL_CLIENT: ModelClientConfig = {
  provider: "autogen_ext.models.openai.OpenAIChatCompletionClient",
  component_type: "model",
  config: { model: "gpt-4o-mini", temperature: 0.7 },
};

export const DEFAULT_TERMINATION: TerminationConfig = {
  provider: "autogen_agentchat.conditions.TextMentionTermination",
  component_type: "termination",
  config: { text: "TERMINATE" },
};

// ============================================
// PART 1: JSON → PatternDefinition (UI용)
// ============================================

/**
 * CoHub JSON을 Frontend PatternDefinition으로 변환
 *
 * 우선순위:
 * 1. JSON의 visual_override 필드 (있으면 사용)
 * 2. providers.json의 기본값
 */
export function convertToPatternDefinition(json: CoHubPatternJSON): PatternDefinition {
  const providerFull = json.autogen_implementation.provider;
  const providerShort = extractProviderShort(providerFull);

  // providers.json에서 기본값 로드
  const baseCategory = getCategory(providerFull);
  const baseLayout = getLayout(providerFull);
  const baseIcon = getIcon(providerFull);
  const baseColors = getColors(providerFull);

  // JSON의 visual_override 확인 (패턴별 커스텀)
  const override = (json as any).visual_override || {};

  // Visual 설정 (override > base)
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

  return {
    id: json.id,
    name: json.name.en,
    category: override.category || baseCategory,
    description: json.description.en,
    useCases: json.when_to_use.slice(0, 3),

    structure: {
      requiresCoordinator: requiresModelClient(providerFull) || providerShort === "Swarm",
      coordinatorRole: getCoordinatorRole(providerShort),
      minAgents: getMinAgents(json),
      maxAgents: undefined,
      agentRoles: getAgentRoles(json),
    },

    communication: {
      style: getCommunicationStyle(providerFull),
      connections: getConnections(providerFull),
    },

    visual,

    autogenProvider: providerShort,
    autogenProviderFull: providerFull,

    requiredConfig: getRequiredConfig(providerShort),
    prompts: getPrompts(json),

    complexity: json.complexity,
    pros: json.pros,
    cons: json.cons,
    bestPractices: json.best_practices,
    references: json.references,
  };
}

// ============================================
// PART 2: JSON → TeamConfig (Runtime용)
// ============================================

/**
 * CoHub JSON을 Runtime TeamConfig로 변환
 */
export function buildTeamTemplate(
  json: CoHubPatternJSON,
  options: {
    modelClient?: ModelClientConfig;
    terminationCondition?: TerminationConfig;
    language?: "en" | "ko";
  } = {}
): Component<TeamConfig> {
  const modelClient = options.modelClient || DEFAULT_MODEL_CLIENT;
  const termination = options.terminationCondition || DEFAULT_TERMINATION;
  const lang = options.language || "en";

  const providerFull = json.autogen_implementation.provider;
  const providerShort = extractProviderShort(providerFull);

  // Participants 빌드
  const participants = buildParticipants(json, modelClient, lang);

  // Team config
  const teamConfig: TeamConfig = {
    participants,
    termination_condition: termination,
  };

  // model_client 필요 시 추가
  if (requiresModelClient(providerFull)) {
    teamConfig.model_client = modelClient;
  }

  // SelectorGroupChat 전용 설정
  if (providerShort === "SelectorGroupChat") {
    teamConfig.selector_prompt =
      json.autogen_implementation.team_config?.selector_prompt ||
      buildDefaultSelectorPrompt(json);
    teamConfig.allow_repeated_speaker = true;
  }

  return {
    provider: providerFull,
    component_type: "team",
    config: teamConfig,
  };
}

// ============================================
// 헬퍼 함수들
// ============================================

function getCoordinatorRole(provider: string): string | undefined {
  const roles: Record<string, string> = {
    SelectorGroupChat: "LLM Selector",
    Swarm: "Triage Agent",
    MagenticOneGroupChat: "Orchestrator",
  };
  return roles[provider];
}

function getMinAgents(json: CoHubPatternJSON): number {
  const participants = json.autogen_implementation.team_config?.participants;
  return participants ? Math.max(2, participants.length) : 2;
}

function getAgentRoles(json: CoHubPatternJSON): string[] {
  const participants = json.autogen_implementation.team_config?.participants;
  if (!participants) return [];
  return participants.map((p) => p.config.name);
}

function getRequiredConfig(provider: string): PatternDefinition["requiredConfig"] {
  if (provider === "SelectorGroupChat" || provider === "MagenticOneGroupChat") {
    return {
      model_client: {
        provider: "autogen_ext.models.openai.OpenAIChatCompletionClient",
        config: { model: "gpt-4o-mini" },
      },
      allow_repeated_speaker: provider === "SelectorGroupChat",
    };
  }
  return undefined;
}

function getPrompts(json: CoHubPatternJSON): PatternDefinition["prompts"] {
  const selectorPrompt = json.autogen_implementation.team_config?.selector_prompt;
  return selectorPrompt ? { selector: selectorPrompt } : undefined;
}

function buildParticipants(
  json: CoHubPatternJSON,
  modelClient: ModelClientConfig,
  lang: "en" | "ko"
): Array<{ provider: string; component_type: "agent"; config: AgentConfig }> {
  const teamConfig = json.autogen_implementation.team_config;
  const providerFull = json.autogen_implementation.provider;
  const providerShort = extractProviderShort(providerFull);

  // JSON에 participants가 있으면 사용
  if (teamConfig?.participants && teamConfig.participants.length > 0) {
    return teamConfig.participants.map((p) => ({
      provider: p.provider || "autogen_agentchat.agents.AssistantAgent",
      component_type: "agent" as const,
      config: {
        name: p.config.name,
        description: p.config.description,
        system_message: p.config.system_message,
        model_client: modelClient,
        ...(p.config.handoffs ? { handoffs: p.config.handoffs } : {}),
      },
    }));
  }

  // 없으면 providers.json의 기본값 사용
  const defaults = getDefaultParticipants(providerFull, lang);

  return defaults.map((p, index) => {
    const config: AgentConfig = {
      name: p.name,
      description: p.description,
      system_message: p.systemMessage,
      model_client: modelClient,
    };

    // Swarm: 첫 에이전트에 handoffs 추가
    if (providerShort === "Swarm" && index === 0) {
      config.handoffs = defaults.slice(1).map((x) => x.name);
    }

    return {
      provider: "autogen_agentchat.agents.AssistantAgent",
      component_type: "agent" as const,
      config,
    };
  });
}

function buildDefaultSelectorPrompt(json: CoHubPatternJSON): string {
  return `You are coordinating a team for: ${json.name.en}

Available agents:
{roles}

Based on the conversation, select the BEST agent to respond next.
Consider: expertise match, task requirements, conversation flow.

{history}

Select from: {participants}
Respond with ONLY the agent name.`;
}

// ============================================
// 배치 변환 함수
// ============================================

export function convertAllPatterns(jsons: CoHubPatternJSON[]): PatternDefinition[] {
  return jsons.map(convertToPatternDefinition).sort((a, b) => a.id.localeCompare(b.id));
}

export function buildAllTemplates(
  jsons: CoHubPatternJSON[],
  options?: Parameters<typeof buildTeamTemplate>[1]
): Record<string, Component<TeamConfig>> {
  const templates: Record<string, Component<TeamConfig>> = {};
  for (const json of jsons) {
    templates[json.id] = buildTeamTemplate(json, options);
  }
  return templates;
}
