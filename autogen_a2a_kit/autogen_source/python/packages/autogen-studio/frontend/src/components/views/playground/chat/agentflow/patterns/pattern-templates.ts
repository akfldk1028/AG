/**
 * Pattern Templates - Complete Team Configuration Templates
 *
 * ## 변경사항
 * 기존: 이 파일에 ~400줄의 하드코딩된 템플릿
 * 변경: data/*.json에서 자동 생성 (pattern-loader.ts 사용)
 *
 * 새 템플릿 추가 시:
 * 1. AG_Cohub/patterns/에 JSON 파일 추가
 * 2. data/ 폴더에 복사
 * 3. pattern-loader.ts의 import에 추가
 * 4. 끝! (이 파일 수정 불필요)
 */

import { Component, TeamConfig, AgentConfig } from "../../../../../types/datamodel";

// ============================================
// RE-EXPORTS from pattern-loader.ts
// ============================================

export {
  DEFAULT_MODEL_CLIENT,
  DEFAULT_TERMINATION,
  LOADED_PATTERN_TEMPLATES as PATTERN_TEMPLATES,
  getLoadedPatternTemplate as getPatternTemplate,
} from "./pattern-loader";

// Import for local use
import {
  DEFAULT_MODEL_CLIENT,
  LOADED_PATTERN_TEMPLATES as PATTERN_TEMPLATES,
} from "./pattern-loader";

// ============================================
// ADDITIONAL TERMINATION CONDITIONS
// ============================================

/**
 * Max message termination (as fallback)
 */
export const MAX_MESSAGE_TERMINATION = {
  provider: "autogen_agentchat.conditions.MaxMessageTermination",
  component_type: "termination" as const,
  config: {
    max_messages: 20,
  },
};

/**
 * Combined termination (text OR max messages)
 */
export const COMBINED_TERMINATION = {
  provider: "autogen_agentchat.conditions.CombinedTermination",
  component_type: "termination" as const,
  config: {
    conditions: [
      {
        provider: "autogen_agentchat.conditions.TextMentionTermination",
        component_type: "termination",
        config: { text: "TERMINATE" },
      },
      MAX_MESSAGE_TERMINATION,
    ],
  },
};

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * AssistantAgent 필수 필드 기본값
 */
const ASSISTANT_AGENT_DEFAULTS = {
  reflect_on_tool_use: false,
  tool_call_summary_format: "{result}",
  model_client_stream: false,
};

/**
 * Create a basic agent configuration
 * Includes all required fields for AssistantAgentConfig
 */
export const createAgentConfig = (
  name: string,
  description: string,
  systemMessage?: string,
  modelClient = DEFAULT_MODEL_CLIENT
): Component<AgentConfig> => ({
  provider: "autogen_agentchat.agents.AssistantAgent",
  component_type: "agent" as const,
  config: {
    name,
    description,
    system_message: systemMessage || `You are ${name}. ${description}`,
    model_client: modelClient,
    // AssistantAgent 필수 필드
    ...ASSISTANT_AGENT_DEFAULTS,
  } as AgentConfig,
});

/**
 * Get all available pattern IDs
 */
export const getAvailablePatternIds = (): string[] => {
  return Object.keys(PATTERN_TEMPLATES);
};

/**
 * Clone a template with deep copy
 */
export const cloneTemplate = (
  template: Component<TeamConfig>
): Component<TeamConfig> => {
  return JSON.parse(JSON.stringify(template));
};

/**
 * Create team config from pattern with custom participants
 *
 * This merges user's agents with the pattern's structure
 */
export const createTeamFromPattern = (
  patternId: string,
  customParticipants?: Component<AgentConfig>[],
  customModelClient?: typeof DEFAULT_MODEL_CLIENT
): Component<TeamConfig> | null => {
  const template = PATTERN_TEMPLATES[patternId];
  if (!template) return null;

  const teamConfig = cloneTemplate(template);
  const config = teamConfig.config as any;

  // Replace model_client if custom one provided
  if (customModelClient) {
    // Update team-level model_client (for SelectorGroupChat)
    if (config.model_client) {
      config.model_client = customModelClient;
    }

    // Update each participant's model_client
    if (config.participants) {
      config.participants = config.participants.map((p: any) => {
        if (p.config?.model_client) {
          return {
            ...p,
            config: {
              ...p.config,
              model_client: customModelClient,
            },
          };
        }
        return p;
      });
    }
  }

  // Replace participants if custom ones provided
  if (customParticipants && customParticipants.length > 0) {
    // Ensure each participant has model_client
    config.participants = customParticipants.map((p) => {
      const participantConfig = p.config as any;
      if (!participantConfig?.model_client) {
        return {
          ...p,
          config: {
            ...participantConfig,
            model_client: customModelClient || DEFAULT_MODEL_CLIENT,
          },
        };
      }
      return p;
    });
  }

  return teamConfig;
};

export default {
  PATTERN_TEMPLATES,
  getPatternTemplate: (id: string) => PATTERN_TEMPLATES[id],
  getAvailablePatternIds,
  cloneTemplate,
  createTeamFromPattern,
  createAgentConfig,
  DEFAULT_MODEL_CLIENT,
  MAX_MESSAGE_TERMINATION,
  COMBINED_TERMINATION,
};
