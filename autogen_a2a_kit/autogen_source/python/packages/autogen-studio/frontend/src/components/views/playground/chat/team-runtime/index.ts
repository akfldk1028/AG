/**
 * Team Runtime Module
 *
 * Converts visual pattern selections to actual AutoGen team configurations.
 * Separated from pattern-schema (visualization) for clean architecture.
 *
 * Key components:
 * - pattern-runtime: Main orchestrator for applying patterns
 * - team-factory: Creates complete team configurations from patterns
 * - *-config: Pattern-specific configuration helpers
 */

// Main pattern runtime functions
export {
  applyPatternToTeam,
  applyPatternComplete,
  validateTeamForExecution,
  ensureTeamReady,
  getCompatiblePatterns,
  isPatternCompatible,
  generateRoleDescriptions,
  fillSelectorPrompt,
  type PatternApplyResult,
  type PatternApplyOptions,
} from './pattern-runtime';

// Team factory for creating complete team configurations
export {
  createNewTeamFromPattern,
  applyPatternToExistingTeam,
  createOrModifyTeam,
  validateTeamConfig,
  getRecommendedPattern,
  getAvailablePatterns,
  type TeamFactoryOptions,
  type TeamFactoryResult,
} from './team-factory';

// Pattern-specific configuration helpers
export { configureSwarm, type SwarmConfigOptions } from './swarm-config';
export { configureSelector, type SelectorConfigOptions } from './selector-config';
export { configureRoundRobin, type RoundRobinConfigOptions } from './roundrobin-config';

// Re-export model client for convenience
export { DEFAULT_MODEL_CLIENT } from '../agentflow/patterns/pattern-templates';
