/**
 * Pattern Module Index
 *
 * Exports all pattern generators and provides pattern detection logic.
 * Now uses abstract JSON-based pattern definitions for extensibility.
 */

import {
  Component,
  AgentConfig,
  TeamConfig,
  Run,
} from "../../../../../types/datamodel";
import { PatternType, PatternLayoutResult, PatternGenerator } from "./types";
import { generateSequentialLayout } from "./sequential-pattern";
import { generateSelectorLayout } from "./selector-pattern";
import { generateHandoffLayout } from "./handoff-pattern";

// New pattern schema system
import {
  PATTERN_LIBRARY,
  PatternDefinition,
  PatternCategory,
  getPatternById,
  getPatternsByCategory,
} from "./pattern-schema";
import { generateLayoutFromPattern } from "./layout-generator";

// Export types and constants
export * from "./types";
export { NODE_DIMENSIONS } from "./types";

// Export individual pattern generators (legacy)
export { generateSequentialLayout } from "./sequential-pattern";
export { generateSelectorLayout } from "./selector-pattern";
export { generateHandoffLayout } from "./handoff-pattern";

// Export new pattern schema system
export {
  PATTERN_LIBRARY,
  getPatternById,
  getPatternsByCategory,
  getPatternSelectorPrompt,
  getPatternByProvider,
  applyPatternToConfig,
  patternToTeamConfig,
  // New template integration functions
  getDefaultTeamConfig,
  createTeamConfigFromPattern,
  hasPatternTemplate,
  getPatternsWithTemplates,
  DEFAULT_MODEL_CLIENT,
} from "./pattern-schema";
export type { PatternDefinition, PatternCategory } from "./pattern-schema";
export { generateLayoutFromPattern } from "./layout-generator";

// Export pattern templates
export {
  PATTERN_TEMPLATES,
  getPatternTemplate,
  cloneTemplate,
  createTeamFromPattern,
  createAgentConfig,
  DEFAULT_TERMINATION,
  COMBINED_TERMINATION,
} from "./pattern-templates";

/**
 * Detect pattern type from team configuration
 */
export const getPatternType = (
  teamConfig: Component<TeamConfig>
): PatternType => {
  const provider = teamConfig.provider || "";
  const participants = teamConfig.config?.participants || [];

  // Check for Swarm (Handoff pattern)
  if (provider.includes("Swarm")) {
    return "handoff";
  }

  // Check for SelectorGroupChat
  if (provider.includes("SelectorGroupChat")) {
    // Check for debate pattern (advocate, critic, judge)
    const names = participants.map(
      (p: Component<AgentConfig>) => p.config?.name?.toLowerCase() || ""
    );
    if (
      names.some(
        (n: string) =>
          n.includes("advocate") || n.includes("judge") || n.includes("critic")
      )
    ) {
      return "debate";
    }
    return "selector";
  }

  // Check for RoundRobinGroupChat
  if (provider.includes("RoundRobinGroupChat")) {
    // Check for reflection pattern (generator + critic with approval)
    const names = participants.map(
      (p: Component<AgentConfig>) => p.config?.name?.toLowerCase() || ""
    );
    if (
      participants.length === 2 &&
      names.some(
        (n: string) => n.includes("generator") || n.includes("writer")
      ) &&
      names.some((n: string) => n.includes("critic") || n.includes("reviewer"))
    ) {
      return "reflection";
    }
    return "sequential";
  }

  return "unknown";
};

/**
 * Pattern type to label mapping
 */
export const patternLabels: Record<
  PatternType,
  { label: string; color: string; description: string }
> = {
  sequential: {
    label: "Sequential",
    color: "#3b82f6", // blue
    description: "Agents take turns in fixed order",
  },
  selector: {
    label: "Selector",
    color: "#8b5cf6", // purple
    description: "Central router selects best agent",
  },
  handoff: {
    label: "Handoff",
    color: "#f59e0b", // yellow
    description: "Agents dynamically transfer control",
  },
  debate: {
    label: "Debate",
    color: "#ef4444", // red
    description: "Agents argue different perspectives",
  },
  reflection: {
    label: "Reflection",
    color: "#22c55e", // green
    description: "Iterative improvement through feedback",
  },
  unknown: {
    label: "Custom",
    color: "#6b7280", // gray
    description: "Custom team configuration",
  },
};

/**
 * Get pattern generator for a given pattern type
 */
export const getPatternGenerator = (patternType: PatternType): PatternGenerator => {
  switch (patternType) {
    case "sequential":
    case "reflection": // Reflection uses sequential layout for now
      return generateSequentialLayout;
    case "selector":
    case "debate": // Debate uses selector layout with different styling
      return generateSelectorLayout;
    case "handoff":
      return generateHandoffLayout;
    default:
      return generateSequentialLayout; // Default to sequential
  }
};

/**
 * Generate pattern-based layout for a team (Legacy)
 */
export const generatePatternLayout = (
  teamConfig: Component<TeamConfig>,
  participatedAgents: Set<string>,
  run?: Run
): PatternLayoutResult & { patternType: PatternType } => {
  const patternType = getPatternType(teamConfig);
  const generator = getPatternGenerator(patternType);
  const layout = generator(teamConfig, participatedAgents, run);

  return {
    ...layout,
    patternType,
  };
};

/**
 * Generate layout using new pattern schema system
 * Provides more visual distinction between patterns
 */
export const generatePatternLayoutV2 = (
  teamConfig: Component<TeamConfig>,
  participatedAgents: Set<string>,
  run?: Run,
  overridePatternId?: string
): PatternLayoutResult & { patternType: PatternType; patternDef: PatternDefinition | undefined } => {
  // If pattern override is provided, use it
  if (overridePatternId) {
    const patternDef = getPatternById(overridePatternId);
    if (patternDef) {
      const layout = generateLayoutFromPattern(patternDef, teamConfig, participatedAgents, run);
      return {
        ...layout,
        patternType: overridePatternId as PatternType,
        patternDef,
      };
    }
  }

  // Otherwise detect from team config
  const patternType = getPatternType(teamConfig);

  // Map legacy pattern types to new pattern IDs
  const patternIdMap: Record<PatternType, string> = {
    sequential: "sequential",
    selector: "selector",
    handoff: "swarm",
    debate: "debate",
    reflection: "reflection",
    unknown: "sequential",
  };

  const patternId = patternIdMap[patternType];
  const patternDef = getPatternById(patternId);

  if (patternDef) {
    const layout = generateLayoutFromPattern(patternDef, teamConfig, participatedAgents, run);
    return {
      ...layout,
      patternType,
      patternDef,
    };
  }

  // Fallback to legacy generator
  const generator = getPatternGenerator(patternType);
  const layout = generator(teamConfig, participatedAgents, run);

  return {
    ...layout,
    patternType,
    patternDef: undefined,
  };
};

/**
 * Get pattern definition from team config
 */
export const getPatternDefinition = (teamConfig: Component<TeamConfig>): PatternDefinition | undefined => {
  const patternType = getPatternType(teamConfig);
  const patternIdMap: Record<PatternType, string> = {
    sequential: "sequential",
    selector: "selector",
    handoff: "swarm",
    debate: "debate",
    reflection: "reflection",
    unknown: "sequential",
  };
  return getPatternById(patternIdMap[patternType]);
};
