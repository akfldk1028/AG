/**
 * RoundRobin Pattern Configuration
 *
 * Configures team for RoundRobinGroupChat patterns:
 * - Sequential/Pipeline
 * - Reflection Loop
 * - Removes selector-specific configs
 */

export interface RoundRobinConfigOptions {
  /** Maximum rounds for reflection pattern */
  maxRounds?: number;
}

/**
 * Configure a team for RoundRobinGroupChat pattern
 */
export const configureRoundRobin = (
  config: any,
  options: RoundRobinConfigOptions = {}
): void => {
  // Remove selector-specific configs (not needed for round robin)
  delete config.model_client;
  delete config.selector_prompt;
  delete config.allow_repeated_speaker;

  // Remove handoffs (not used in round robin)
  if (config.participants && Array.isArray(config.participants)) {
    config.participants = config.participants.map((participant: any) => {
      const modifiedParticipant = JSON.parse(JSON.stringify(participant));
      if (modifiedParticipant.config) {
        delete modifiedParticipant.config.handoffs;
      }
      return modifiedParticipant;
    });
  }
};

export default configureRoundRobin;
