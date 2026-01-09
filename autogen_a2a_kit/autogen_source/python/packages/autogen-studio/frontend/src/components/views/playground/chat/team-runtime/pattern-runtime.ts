/**
 * Pattern Runtime - Main Orchestrator
 *
 * Converts pattern selection to actual team runtime configuration.
 * This is the core module that bridges visual patterns with AutoGen execution.
 *
 * Updated to use team-factory for complete configuration generation.
 */

import { Component, TeamConfig, AgentConfig } from "../../../../types/datamodel";
import { PatternDefinition, getPatternById, PATTERN_LIBRARY } from "../agentflow/patterns/pattern-schema";
import { configureSwarm, SwarmConfigOptions } from "./swarm-config";
import { configureSelector, SelectorConfigOptions } from "./selector-config";
import { configureRoundRobin, RoundRobinConfigOptions } from "./roundrobin-config";
import {
  createOrModifyTeam,
  validateTeamConfig,
  TeamFactoryOptions,
  TeamFactoryResult,
} from "./team-factory";
import { DEFAULT_MODEL_CLIENT } from "../agentflow/patterns/pattern-templates";

/**
 * Options for applying a pattern to a team
 */
export interface PatternApplyOptions {
  swarm?: SwarmConfigOptions;
  selector?: SelectorConfigOptions;
  roundRobin?: RoundRobinConfigOptions;
}

/**
 * Result of applying a pattern
 */
export interface PatternApplyResult {
  /** The modified team configuration */
  teamConfig: Component<TeamConfig>;
  /** Whether the pattern required provider change */
  providerChanged: boolean;
  /** Any warnings about the configuration */
  warnings: string[];
  /** The pattern that was applied */
  appliedPattern: PatternDefinition | null;
}

/**
 * Apply a pattern to a team configuration
 *
 * This is the main function that transforms a team configuration
 * to match the selected pattern's requirements.
 *
 * @param teamConfig - The original team configuration
 * @param patternId - The ID of the pattern to apply
 * @param options - Configuration options for each pattern type
 * @returns The modified team configuration with metadata
 */
export const applyPatternToTeam = (
  teamConfig: Component<TeamConfig>,
  patternId: string,
  options: PatternApplyOptions = {}
): PatternApplyResult => {
  const pattern = getPatternById(patternId);

  if (!pattern) {
    return {
      teamConfig,
      providerChanged: false,
      warnings: [`Pattern '${patternId}' not found in library`],
      appliedPattern: null,
    };
  }

  // Deep clone the teamConfig
  const modifiedConfig = JSON.parse(
    JSON.stringify(teamConfig)
  ) as Component<TeamConfig>;

  // Track original provider for comparison
  const originalProvider = modifiedConfig.provider;
  const warnings: string[] = [];

  // Update the provider from pattern schema
  modifiedConfig.provider = pattern.autogenProviderFull;

  const config = modifiedConfig.config as any;
  const participants = (config?.participants || []) as Component<AgentConfig>[];

  // Apply pattern-specific configuration based on provider type
  switch (pattern.autogenProvider) {
    case "Swarm":
      configureSwarm(config, participants, options.swarm || {});
      break;

    case "SelectorGroupChat":
      const selectorResult = configureSelector(
        config,
        pattern,
        options.selector || {}
      );
      warnings.push(...selectorResult.warnings);
      break;

    case "RoundRobinGroupChat":
      configureRoundRobin(config, options.roundRobin || {});
      break;

    default:
      warnings.push(`Unknown provider: ${pattern.autogenProvider}`);
  }

  return {
    teamConfig: modifiedConfig,
    providerChanged: originalProvider !== pattern.autogenProviderFull,
    warnings,
    appliedPattern: pattern,
  };
};

/**
 * Get compatible patterns for a given team provider
 *
 * Returns patterns that can be applied to a team with minimal changes.
 *
 * @param provider - The team's current provider string
 * @returns Array of compatible pattern definitions
 */
export const getCompatiblePatterns = (
  provider: string
): PatternDefinition[] => {
  // Map provider to its pattern family
  const providerToFamily: Record<string, string[]> = {
    RoundRobinGroupChat: ["sequential", "reflection"],
    SelectorGroupChat: ["selector", "parallel", "debate", "supervisor"],
    Swarm: ["swarm", "hierarchical"],
  };

  // Find which family this provider belongs to
  for (const [key, patternIds] of Object.entries(providerToFamily)) {
    if (provider.includes(key)) {
      return patternIds
        .map((id) => getPatternById(id))
        .filter((p): p is PatternDefinition => p !== undefined);
    }
  }

  // Default: return all patterns
  return PATTERN_LIBRARY;
};

/**
 * Check if a pattern is compatible with a team's provider
 *
 * @param provider - The team's current provider string
 * @param patternId - The pattern to check
 * @returns true if the pattern is natively compatible
 */
export const isPatternCompatible = (
  provider: string,
  patternId: string
): boolean => {
  const pattern = getPatternById(patternId);
  if (!pattern) return false;

  return provider.includes(pattern.autogenProvider);
};

/**
 * Generate participant role descriptions for selector prompt
 *
 * @param participants - Array of participant configurations
 * @returns Formatted role descriptions string
 */
export const generateRoleDescriptions = (
  participants: Component<AgentConfig>[]
): string => {
  return participants
    .map((p) => {
      const name = p.config?.name || p.label || "Agent";
      const description = p.config?.description || p.description || "No description";
      return `- ${name}: ${description}`;
    })
    .join("\n");
};

/**
 * Fill selector prompt placeholders with actual values
 *
 * @param prompt - The selector prompt template
 * @param participants - Array of participant configurations
 * @param history - Optional conversation history
 * @returns The filled prompt string
 */
export const fillSelectorPrompt = (
  prompt: string,
  participants: Component<AgentConfig>[],
  history?: string
): string => {
  const roles = generateRoleDescriptions(participants);
  const names = participants
    .map((p) => p.config?.name || p.label)
    .filter(Boolean)
    .join(", ");

  return prompt
    .replace("{roles}", roles)
    .replace("{participants}", names)
    .replace("{history}", history || "[No history yet]");
};

// ============================================
// ENHANCED PATTERN APPLICATION (using team-factory)
// ============================================

/**
 * Apply pattern to team with complete configuration
 *
 * This is the recommended function for applying patterns.
 * It uses team-factory to ensure all required config is present.
 *
 * @param teamConfig - The original team configuration
 * @param patternId - The ID of the pattern to apply
 * @param options - Factory options for customization
 */
export const applyPatternComplete = (
  teamConfig: Component<TeamConfig> | null,
  patternId: string,
  options: TeamFactoryOptions = {}
): TeamFactoryResult => {
  return createOrModifyTeam(teamConfig, patternId, options);
};

/**
 * Validate that a team is ready to run
 *
 * Checks for:
 * - Valid provider
 * - Participants with model_client
 * - Required pattern-specific config (e.g., selector_prompt)
 */
export const validateTeamForExecution = (
  teamConfig: Component<TeamConfig>
): { valid: boolean; errors: string[]; warnings: string[] } => {
  const validation = validateTeamConfig(teamConfig);
  const warnings: string[] = [];
  const config = teamConfig.config as any;

  // Additional checks
  if (teamConfig.provider?.includes("SelectorGroupChat")) {
    if (!config?.selector_prompt) {
      warnings.push("SelectorGroupChat without selector_prompt may use default behavior");
    }
  }

  if (!config?.termination_condition) {
    warnings.push("No termination_condition set - task may run indefinitely");
  }

  return {
    valid: validation.valid,
    errors: validation.errors,
    warnings,
  };
};

/**
 * Ensure team config is complete and ready to execute
 *
 * This is a convenience function that:
 * 1. Applies the pattern if needed
 * 2. Validates the configuration
 * 3. Returns a ready-to-run config or errors
 */
export const ensureTeamReady = (
  teamConfig: Component<TeamConfig>,
  patternId?: string
): {
  teamConfig: Component<TeamConfig>;
  isReady: boolean;
  errors: string[];
  warnings: string[];
} => {
  let finalConfig = teamConfig;
  const allWarnings: string[] = [];

  // Apply pattern if specified
  if (patternId) {
    const result = applyPatternComplete(teamConfig, patternId);
    finalConfig = result.teamConfig;
    allWarnings.push(...result.warnings);
  }

  // Validate
  const validation = validateTeamForExecution(finalConfig);

  return {
    teamConfig: finalConfig,
    isReady: validation.valid,
    errors: validation.errors,
    warnings: [...allWarnings, ...validation.warnings],
  };
};

// Re-export factory functions for convenience
export { createOrModifyTeam, validateTeamConfig } from "./team-factory";
export { DEFAULT_MODEL_CLIENT };

export default {
  applyPatternToTeam,
  applyPatternComplete,
  validateTeamForExecution,
  ensureTeamReady,
  getCompatiblePatterns,
  isPatternCompatible,
  generateRoleDescriptions,
  fillSelectorPrompt,
};
