/**
 * Team Factory - Creates complete team configurations from patterns
 *
 * This is the main entry point for creating teams that are ready to execute.
 * It bridges:
 * - Pattern selection (user picks a collaboration style)
 * - Template system (pre-configured team structures)
 * - Custom participants (user's actual agents)
 * - Runtime configuration (model_client, termination, etc.)
 */

import { Component, TeamConfig, AgentConfig } from "../../../../types/datamodel";
import {
  getPatternById,
  PatternDefinition,
  PATTERN_LIBRARY,
} from "../agentflow/patterns/pattern-schema";
import {
  getPatternTemplate,
  cloneTemplate,
  DEFAULT_MODEL_CLIENT,
  DEFAULT_TERMINATION,
  COMBINED_TERMINATION,
  createAgentConfig,
} from "../agentflow/patterns/pattern-templates";

/**
 * Agent info for dynamic prompt generation
 */
interface AgentInfo {
  name: string;
  description: string;
}

/**
 * Generate dynamic selector_prompt based on actual agents (name + description)
 * This allows A2A agents to participate in any pattern.
 *
 * A2A Integration: A2A agents have both name and description.
 * The selector LLM needs descriptions to make intelligent speaker selection.
 */
const generateDynamicSelectorPrompt = (
  patternId: string,
  agents: AgentInfo[]
): string => {
  const names = agents.map(a => a.name).join(", ");
  const agentList = agents.map(a =>
    `- ${a.name}: ${a.description || "No description"}`
  ).join("\n");

  // Pattern-specific prompt templates
  const promptTemplates: Record<string, string> = {
    debate: `You are coordinating a multi-agent debate. You MUST rotate between different agents.

Available Agents:
${agentList}

CRITICAL RULES:
1. **NEVER select the same agent twice in a row** - you MUST choose a DIFFERENT agent than the last speaker
2. Each agent must take turns presenting their unique perspective
3. Ensure ALL agents participate by rotating through them fairly
4. If Agent A just spoke, select Agent B or Agent C next - NEVER Agent A again

Based on the conversation history, select the NEXT speaker (must be different from the last one).
Consider:
- Who just spoke? Select someone DIFFERENT
- Has everyone had a chance to speak?
- Whose expertise complements the current discussion?

Available agents: ${names}
Return ONLY the agent name, nothing else. The agent MUST be different from the last speaker.`,

    selector: `You are a smart agent selector.

Available Agents:
${agentList}

Based on the conversation history and the current request, choose the agent whose expertise best matches the needs.

Available agents: ${names}
Return ONLY the agent name, nothing else.`,

    reflection: `You are coordinating a reflection/review pattern.

Available Agents:
${agentList}

Pattern: One agent produces work, another reviews and provides feedback.
Based on the conversation, select who should respond next.

Available agents: ${names}
Return ONLY the agent name, nothing else.`,

    default: `Select the next agent to speak.

Available Agents:
${agentList}

Based on the conversation history, choose the most appropriate agent to continue.
Consider each agent's expertise and the current topic.

Return ONLY the agent name, nothing else.`
  };

  return promptTemplates[patternId] || promptTemplates.default;
};

/**
 * Options for creating a team from a pattern
 */
export interface TeamFactoryOptions {
  /** Custom model client to use (overrides default) */
  modelClient?: {
    provider: string;
    component_type: "model";
    config: Record<string, unknown>;
  };
  /** Custom termination condition */
  terminationCondition?: {
    provider: string;
    component_type: "termination";
    config: Record<string, unknown>;
  };
  /** Whether to use combined termination (text + max messages) */
  useCombinedTermination?: boolean;
  /** Max messages for max message termination */
  maxMessages?: number;
  /** Preserve existing team's model_client if available */
  preserveExistingModelClient?: boolean;
}

/**
 * Result of team factory operation
 */
export interface TeamFactoryResult {
  /** The created/modified team configuration */
  teamConfig: Component<TeamConfig>;
  /** Pattern that was applied */
  pattern: PatternDefinition | null;
  /** Whether a new team was created vs modified */
  isNewTeam: boolean;
  /** Any warnings during creation */
  warnings: string[];
  /** Whether model_client was added/modified */
  modelClientModified: boolean;
}

/**
 * Model client type for team factory
 */
type ModelClientConfig = {
  provider: string;
  component_type: "model";
  config: Record<string, unknown>;
};

/**
 * AssistantAgent 필수 필드 기본값
 * AutoGen의 AssistantAgentConfig는 이 필드들이 필수입니다.
 */
const ASSISTANT_AGENT_DEFAULTS = {
  reflect_on_tool_use: false,
  tool_call_summary_format: "{result}",
  model_client_stream: false,
};

/**
 * Ensure an agent has model_client and required fields configured
 * For AssistantAgent, this also ensures reflect_on_tool_use, tool_call_summary_format, model_client_stream
 */
const ensureAgentModelClient = (
  agent: Component<AgentConfig>,
  defaultClient: ModelClientConfig
): Component<AgentConfig> => {
  const config = agent.config as any;
  const isAssistantAgent = agent.provider?.includes("AssistantAgent");

  // 필수 필드들이 이미 설정되어 있는지 확인
  const needsModelClient = !config?.model_client;
  const needsAssistantDefaults = isAssistantAgent && (
    config?.reflect_on_tool_use === undefined ||
    config?.tool_call_summary_format === undefined ||
    config?.model_client_stream === undefined
  );

  if (needsModelClient || needsAssistantDefaults) {
    return {
      ...agent,
      config: {
        ...config,
        ...(needsModelClient ? { model_client: { ...defaultClient } } : {}),
        ...(needsAssistantDefaults ? ASSISTANT_AGENT_DEFAULTS : {}),
      },
    };
  }
  return agent;
};

/**
 * Create a completely new team from a pattern template
 *
 * This creates a fresh team using the pattern's default structure.
 * Use this when starting from scratch.
 */
export const createNewTeamFromPattern = (
  patternId: string,
  options: TeamFactoryOptions = {}
): TeamFactoryResult => {
  const warnings: string[] = [];
  const pattern = getPatternById(patternId);

  if (!pattern) {
    return {
      teamConfig: createFallbackTeam(),
      pattern: null,
      isNewTeam: true,
      warnings: [`Pattern '${patternId}' not found, using fallback sequential team`],
      modelClientModified: true,
    };
  }

  const template = getPatternTemplate(patternId);
  if (!template) {
    return {
      teamConfig: createFallbackTeam(),
      pattern,
      isNewTeam: true,
      warnings: [`No template for pattern '${patternId}', using fallback team`],
      modelClientModified: true,
    };
  }

  // Deep clone the template
  const teamConfig = cloneTemplate(template);
  const config = teamConfig.config as any;

  // Apply custom model client if provided
  const modelClient: ModelClientConfig = options.modelClient || DEFAULT_MODEL_CLIENT;
  let modelClientModified = false;

  // Update team-level model_client (for SelectorGroupChat)
  if (config.model_client) {
    config.model_client = { ...modelClient };
    modelClientModified = true;
  }

  // Update each participant's model_client
  if (config.participants) {
    config.participants = config.participants.map((p: Component<AgentConfig>) => {
      const updated = ensureAgentModelClient(p, modelClient);
      if (updated !== p) modelClientModified = true;
      return updated;
    });
  }

  // Apply custom termination condition
  if (options.useCombinedTermination) {
    const combinedTerm = { ...COMBINED_TERMINATION };
    if (options.maxMessages) {
      (combinedTerm.config as any).conditions[1].config.max_messages = options.maxMessages;
    }
    config.termination_condition = combinedTerm;
  } else if (options.terminationCondition) {
    config.termination_condition = options.terminationCondition;
  }

  return {
    teamConfig,
    pattern,
    isNewTeam: true,
    warnings,
    modelClientModified,
  };
};

/**
 * Apply a pattern to an existing team configuration
 *
 * This changes the team structure to match the selected pattern while
 * PRESERVING existing agents (including A2A agents).
 *
 * A2A Integration: A2A agents can participate in ANY pattern.
 * The pattern defines the STRUCTURE (SelectorGroupChat, RoundRobin, etc.),
 * not the specific agents. Existing agents are always kept.
 */
export const applyPatternToExistingTeam = (
  existingTeam: Component<TeamConfig>,
  patternId: string,
  options: TeamFactoryOptions = {}
): TeamFactoryResult => {
  const warnings: string[] = [];
  const pattern = getPatternById(patternId);

  if (!pattern) {
    warnings.push(`Pattern '${patternId}' not found, returning original team`);
    return {
      teamConfig: existingTeam,
      pattern: null,
      isNewTeam: false,
      warnings,
      modelClientModified: false,
    };
  }

  const existingParticipants = (existingTeam.config as any)?.participants || [];
  const existingParticipantCount = existingParticipants.length;
  const patternMinAgents = pattern.structure?.minAgents || 2;

  // Get existing agent info (name + description) for selector prompt generation
  // A2A agents have both name and description fields
  const existingAgents: AgentInfo[] = existingParticipants.map(
    (p: Component<AgentConfig>) => ({
      name: (p.config?.name || "unnamed") as string,
      description: (p.config?.description || p.description || "") as string
    })
  );
  const existingAgentNames = existingAgents.map(a => a.name);

  // ===== DEBUG: Pattern Application =====
  console.log(`🔍 APPLY PATTERN TO EXISTING TEAM:
    patternId: "${patternId}"
    patternProvider: "${pattern.autogenProviderFull}"
    patternMinAgents: ${patternMinAgents}
    existingParticipantCount: ${existingParticipantCount}
    existingAgents: ${JSON.stringify(existingAgents, null, 2)}
    action: ${existingParticipantCount === 0 ? "CREATE NEW (no agents)" : "KEEP EXISTING AGENTS"}
  `);

  // Only create new team if there are NO existing agents
  // A2A agents should always be preserved!
  if (existingParticipantCount === 0) {
    console.log("✅ No existing agents - creating from pattern template");
    warnings.push(`No existing agents. Using pattern's default agents.`);
    return createNewTeamFromPattern(patternId, options);
  }
  console.log(`✅ Keeping ${existingParticipantCount} existing agents and applying ${patternId} structure`);

  // Deep clone existing team
  const teamConfig = JSON.parse(JSON.stringify(existingTeam)) as Component<TeamConfig>;
  const config = teamConfig.config as any;
  // Note: existingParticipants already defined above

  // Get template for pattern-specific config
  const template = getPatternTemplate(patternId);
  const templateConfig = template?.config as any;

  // Update provider to match pattern
  teamConfig.provider = pattern.autogenProviderFull;

  // Determine model client to use
  let modelClient: ModelClientConfig;
  let modelClientModified = false;

  if (options.modelClient) {
    modelClient = options.modelClient;
    modelClientModified = true;
  } else if (options.preserveExistingModelClient && config?.model_client) {
    modelClient = config.model_client;
  } else {
    modelClient = DEFAULT_MODEL_CLIENT;
    modelClientModified = true;
  }

  // Add team-level model_client for selector patterns
  if (pattern.autogenProvider === "SelectorGroupChat") {
    if (!config.model_client || !options.preserveExistingModelClient) {
      config.model_client = { ...modelClient };
      modelClientModified = true;
    }

    // Generate dynamic selector_prompt based on actual agents (name + description)
    // This allows A2A agents (history_agent, philosophy_agent, etc.) to participate
    // The selector LLM needs descriptions to make intelligent speaker selection
    //
    // IMPORTANT: ALWAYS regenerate selector_prompt when applying a pattern!
    // The agents may have changed since the last time, and the old prompt
    // might only include some of the agents.
    {
      const agentNames = existingAgentNames.join(", ");
      const dynamicPrompt = generateDynamicSelectorPrompt(patternId, existingAgents);
      config.selector_prompt = dynamicPrompt;
      warnings.push(`Generated dynamic selector_prompt for agents: [${agentNames}]`);
      console.log(`📝 Dynamic selector_prompt generated for pattern "${patternId}" with agents:\n${existingAgents.map(a => `  - ${a.name}: ${a.description}`).join('\n')}`);
    }

    // Set allow_repeated_speaker from pattern config
    // DEFAULT: false (matches AutoGen's default behavior)
    // AutoGen docs: "By default, the team will not select the same speaker consecutively"
    // If a pattern needs repeated speakers, set requiredConfig.allow_repeated_speaker: true
    config.allow_repeated_speaker =
      pattern.requiredConfig?.allow_repeated_speaker ?? false;
    console.log(`🔄 allow_repeated_speaker set to: ${config.allow_repeated_speaker} (from pattern "${patternId}")`);
  }

  // Configure handoffs for Swarm patterns
  // Each agent needs a `handoffs` array listing other agents they can transfer to
  if (pattern.autogenProvider === "Swarm") {
    console.log(`🔀 Configuring handoffs for Swarm pattern with ${existingAgentNames.length} agents`);

    // For each agent, set handoffs to all OTHER agents
    config.participants = existingParticipants.map((p: Component<AgentConfig>, idx: number) => {
      const agentName = (p.config?.name || `agent_${idx}`) as string;
      // Get all other agent names as handoff targets
      const handoffTargets = existingAgentNames.filter((name: string) => name !== agentName);

      const agentConfig = p.config as any;

      // Update the agent's handoffs
      const updatedAgent = {
        ...p,
        config: {
          ...agentConfig,
          handoffs: handoffTargets,
          // Also update system_message to instruct about handoffs
          system_message: agentConfig.system_message +
            `\n\n[HANDOFF INSTRUCTION] 다른 전문가의 도움이 필요하면 transfer_to_<agent_name> 함수를 호출하세요. ` +
            `사용 가능한 에이전트: ${handoffTargets.join(', ')}`
        }
      };

      console.log(`  - ${agentName} can handoff to: [${handoffTargets.join(', ')}]`);
      return updatedAgent;
    });

    warnings.push(`Configured handoffs for ${existingAgentNames.length} agents in Swarm pattern`);
  }

  // Ensure all participants have model_client
  // NOTE: Use config.participants (which may have been updated by Swarm handoff config)
  // instead of existingParticipants (which is the original)
  if (config.participants && config.participants.length > 0) {
    config.participants = config.participants.map((p: Component<AgentConfig>) => {
      const updated = ensureAgentModelClient(p, modelClient);
      if (updated !== p) modelClientModified = true;
      return updated;
    });
  } else if (existingParticipants.length > 0) {
    // Fallback to existingParticipants if config.participants not set
    config.participants = existingParticipants.map((p: Component<AgentConfig>) => {
      const updated = ensureAgentModelClient(p, modelClient);
      if (updated !== p) modelClientModified = true;
      return updated;
    });
  }

  // Add termination condition if missing
  if (!config.termination_condition) {
    if (options.useCombinedTermination) {
      config.termination_condition = { ...COMBINED_TERMINATION };
    } else if (options.terminationCondition) {
      config.termination_condition = options.terminationCondition;
    } else {
      config.termination_condition = { ...DEFAULT_TERMINATION };
    }
    warnings.push("Added default termination condition");
  }

  return {
    teamConfig,
    pattern,
    isNewTeam: false,
    warnings,
    modelClientModified,
  };
};

/**
 * Smart team creation - decides whether to create new or modify existing
 *
 * @param existingTeam - Current team config (if any)
 * @param patternId - Pattern to apply
 * @param options - Creation options
 */
export const createOrModifyTeam = (
  existingTeam: Component<TeamConfig> | null | undefined,
  patternId: string,
  options: TeamFactoryOptions = {}
): TeamFactoryResult => {
  // If no existing team or it has no participants, create new
  if (!existingTeam) {
    return createNewTeamFromPattern(patternId, options);
  }

  const config = existingTeam.config as any;
  const hasParticipants =
    config?.participants && config.participants.length > 0;

  if (!hasParticipants) {
    // Existing team shell but no agents - create fresh from template
    return createNewTeamFromPattern(patternId, options);
  }

  // Has participants - preserve them and apply pattern
  return applyPatternToExistingTeam(existingTeam, patternId, options);
};

/**
 * Create a minimal fallback team (sequential with 2 agents)
 */
const createFallbackTeam = (): Component<TeamConfig> => ({
  provider: "autogen_agentchat.teams.RoundRobinGroupChat",
  component_type: "team",
  config: {
    participants: [
      createAgentConfig(
        "Assistant",
        "General purpose assistant",
        "You are a helpful assistant."
      ),
      createAgentConfig(
        "Reviewer",
        "Reviews and validates work",
        "You review work and say TERMINATE when satisfied."
      ),
    ],
    termination_condition: DEFAULT_TERMINATION,
  },
});

/**
 * Validate a team configuration is ready to run
 */
export const validateTeamConfig = (
  teamConfig: Component<TeamConfig>
): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];
  const config = teamConfig.config as any;

  // Check provider
  if (!teamConfig.provider) {
    errors.push("Missing team provider");
  }

  // Check participants
  if (!config?.participants || config.participants.length === 0) {
    errors.push("Team has no participants");
  } else {
    // Check each participant has model_client
    config.participants.forEach((p: any, i: number) => {
      if (!p.config?.model_client) {
        errors.push(`Participant ${i} (${p.config?.name || "unnamed"}) missing model_client`);
      }
    });
  }

  // Check selector patterns have required config
  if (teamConfig.provider?.includes("SelectorGroupChat")) {
    if (!config?.model_client) {
      errors.push("SelectorGroupChat requires team-level model_client");
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
};

/**
 * Get recommended pattern based on number of agents
 */
export const getRecommendedPattern = (agentCount: number): string => {
  if (agentCount <= 2) return "sequential";
  if (agentCount === 2) return "reflection";
  if (agentCount <= 4) return "selector";
  return "swarm";
};

/**
 * Get all available patterns
 */
export const getAvailablePatterns = (): PatternDefinition[] => {
  return PATTERN_LIBRARY;
};

export default {
  createNewTeamFromPattern,
  applyPatternToExistingTeam,
  createOrModifyTeam,
  validateTeamConfig,
  getRecommendedPattern,
  getAvailablePatterns,
};
