/**
 * Selector Pattern Configuration
 *
 * Configures team for SelectorGroupChat patterns:
 * - Adds model_client for LLM-based agent selection
 * - Adds selector_prompt from pattern schema
 * - Sets allow_repeated_speaker
 */

import { PatternDefinition } from "../agentflow/patterns/pattern-schema";

export interface SelectorConfigOptions {
  /** Whether to preserve existing model_client */
  preserveModelClient?: boolean;
  /** Custom model client override */
  customModelClient?: {
    provider: string;
    config: Record<string, unknown>;
  };
  /** Custom selector prompt override */
  customSelectorPrompt?: string;
}

export interface SelectorConfigResult {
  /** Warnings about configuration */
  warnings: string[];
}

/**
 * Configure a team for SelectorGroupChat pattern
 */
export const configureSelector = (
  config: any,
  pattern: PatternDefinition,
  options: SelectorConfigOptions = {}
): SelectorConfigResult => {
  const warnings: string[] = [];
  const requiredConfig = pattern.requiredConfig;

  // Add model_client from schema or options
  if (!config.model_client || !options.preserveModelClient) {
    if (options.customModelClient) {
      config.model_client = options.customModelClient;
    } else if (requiredConfig?.model_client) {
      config.model_client = {
        provider: requiredConfig.model_client.provider,
        config: requiredConfig.model_client.config,
      };
    } else {
      // Default model client for selector
      config.model_client = {
        provider: "autogen_ext.models.openai.OpenAIChatCompletionClient",
        config: { model: "gpt-4o-mini" },
      };
      warnings.push(
        "Using default model_client (gpt-4o-mini) for agent selection"
      );
    }
  }

  // Add selector_prompt from schema or options
  if (!config.selector_prompt) {
    if (options.customSelectorPrompt) {
      config.selector_prompt = options.customSelectorPrompt;
    } else if (pattern.prompts?.selector) {
      config.selector_prompt = pattern.prompts.selector;
    }
  }

  // Set allow_repeated_speaker from schema
  // AutoGen default is FALSE: "By default, the team will not select the same speaker consecutively"
  if (
    config.allow_repeated_speaker === undefined &&
    requiredConfig?.allow_repeated_speaker !== undefined
  ) {
    config.allow_repeated_speaker = requiredConfig.allow_repeated_speaker;
  } else if (config.allow_repeated_speaker === undefined) {
    // Default for selector patterns - FALSE to match AutoGen's default behavior
    // This prevents the same agent from speaking twice in a row (important for debate patterns)
    config.allow_repeated_speaker = false;
  }

  return { warnings };
};

export default configureSelector;
