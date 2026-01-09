/**
 * Abstract Pattern Schema Definition
 *
 * JSON-based pattern definitions for visual flow editing.
 * Each pattern defines:
 * - Structure (how agents are arranged)
 * - Connections (how agents communicate)
 * - Visual representation (layout, colors, icons)
 *
 * ## 패턴 추가 방법
 * 1. data/*.json 파일 추가
 * 2. pattern-loader.ts에 import 추가
 * 3. 끝! (이 파일 수정 불필요)
 *
 * Inspired by:
 * - Strands Agents Collaboration Patterns (AWS)
 * - CrewAI Role-Based Design
 * - LangChain Multi-Agent Architectures
 */

import { Component, TeamConfig, AgentConfig } from "../../../../../types/datamodel";
import {
  getPatternTemplate,
  createTeamFromPattern,
  DEFAULT_MODEL_CLIENT,
} from "./pattern-templates";

// ============================================
// TYPE RE-EXPORTS (from pattern-types.ts)
// ============================================

export type {
  PatternCategory,
  LayoutType,
  PatternVisual,
  PatternConnection,
  PatternDefinition,
} from "./pattern-types";

import type {
  PatternCategory,
  PatternDefinition,
} from "./pattern-types";

// ============================================
// PATTERN LIBRARY (Loaded from JSON!)
// ============================================

/**
 * Pattern Library - Dynamically loaded from JSON files
 *
 * 기존: 이 파일에 ~350줄의 하드코딩된 패턴 정의
 * 변경: data/*.json에서 자동 로드
 *
 * 새 패턴 추가 시:
 * 1. AG_Cohub/patterns/에 JSON 파일 추가
 * 2. data/ 폴더에 복사
 * 3. pattern-loader.ts의 import에 추가
 */
export { LOADED_PATTERN_LIBRARY as PATTERN_LIBRARY } from "./pattern-loader";

// Import for local use in helper functions
import { LOADED_PATTERN_LIBRARY as PATTERN_LIBRARY } from "./pattern-loader";

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Get pattern definition by ID
 */
export const getPatternById = (id: string): PatternDefinition | undefined => {
  return PATTERN_LIBRARY.find(p => p.id === id);
};

/**
 * Get patterns by category
 */
export const getPatternsByCategory = (category: PatternCategory): PatternDefinition[] => {
  return PATTERN_LIBRARY.filter(p => p.category === category);
};

/**
 * Get selector prompt for a pattern (with placeholders)
 */
export const getPatternSelectorPrompt = (patternId: string): string | undefined => {
  const pattern = getPatternById(patternId);
  return pattern?.prompts?.selector;
};

/**
 * Get pattern by AutoGen provider name
 */
export const getPatternByProvider = (provider: string): PatternDefinition | undefined => {
  return PATTERN_LIBRARY.find(p =>
    provider.toLowerCase().includes(p.autogenProvider.toLowerCase())
  );
};

/**
 * Apply pattern configuration to team config
 * This is the ABSTRACT way to configure teams - no hardcoded prompts!
 */
export const applyPatternToConfig = (
  config: Record<string, unknown>,
  patternId: string
): Record<string, unknown> => {
  const pattern = getPatternById(patternId);
  if (!pattern) return config;

  const updatedConfig = { ...config };

  // Apply selector prompt from schema (not hardcoded!)
  if (pattern.prompts?.selector && pattern.autogenProvider === "SelectorGroupChat") {
    updatedConfig.selector_prompt = pattern.prompts.selector;
  }

  // Apply requiredConfig if present
  if (pattern.requiredConfig) {
    if (pattern.requiredConfig.model_client) {
      updatedConfig.model_client = pattern.requiredConfig.model_client;
    }
    if (pattern.requiredConfig.allow_repeated_speaker !== undefined) {
      updatedConfig.allow_repeated_speaker = pattern.requiredConfig.allow_repeated_speaker;
    }
  }

  return updatedConfig;
};

/**
 * Convert pattern definition to team config
 */
export const patternToTeamConfig = (
  pattern: PatternDefinition,
  agents: Array<{ name: string; description: string; tools?: string[] }>
): Record<string, unknown> => {
  const baseConfig: Record<string, unknown> = {
    provider: pattern.autogenProvider,
    component_type: "team",
    config: {
      participants: agents.map((agent) => ({
        provider: "AssistantAgent",
        component_type: "agent",
        config: {
          name: agent.name,
          description: agent.description,
          tools: agent.tools || []
        }
      })),
    }
  };

  // Apply pattern-specific config (prompts, etc.)
  if (baseConfig.config && typeof baseConfig.config === 'object') {
    baseConfig.config = applyPatternToConfig(
      baseConfig.config as Record<string, unknown>,
      pattern.id
    );
  }

  return baseConfig;
};

// ============================================
// TEMPLATE INTEGRATION
// ============================================

/**
 * Get the default team configuration template for a pattern
 *
 * This returns a complete, ready-to-run team config with:
 * - model_client configured
 * - termination_condition set
 * - default participants
 */
export const getDefaultTeamConfig = (
  patternId: string
): Component<TeamConfig> | undefined => {
  return getPatternTemplate(patternId);
};

/**
 * Create a team configuration from a pattern with custom participants
 *
 * @param patternId - The pattern to use as base
 * @param participants - Optional custom participants (will be given model_client)
 * @param modelClient - Optional custom model client
 */
export const createTeamConfigFromPattern = (
  patternId: string,
  participants?: Component<AgentConfig>[],
  modelClient?: typeof DEFAULT_MODEL_CLIENT
): Component<TeamConfig> | null => {
  return createTeamFromPattern(patternId, participants, modelClient);
};

/**
 * Check if a pattern has a valid template
 */
export const hasPatternTemplate = (patternId: string): boolean => {
  return getPatternTemplate(patternId) !== undefined;
};

/**
 * Get all patterns that have complete templates
 */
export const getPatternsWithTemplates = (): PatternDefinition[] => {
  return PATTERN_LIBRARY.filter((p) => hasPatternTemplate(p.id));
};

// Re-export template utilities for convenience
export { DEFAULT_MODEL_CLIENT } from "./pattern-templates";
