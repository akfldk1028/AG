/**
 * Swarm Pattern Configuration
 *
 * Configures team for Swarm (Handoff) pattern:
 * - Adds handoffs between all participants
 * - Removes selector-specific configs (model_client, selector_prompt)
 */

import { Component, AgentConfig } from "../../../../types/datamodel";

export interface SwarmConfigOptions {
  /** Whether to create bidirectional handoffs */
  bidirectional?: boolean;
}

/**
 * Configure a team for Swarm pattern
 */
export const configureSwarm = (
  config: any,
  participants: Component<AgentConfig>[],
  options: SwarmConfigOptions = {}
): void => {
  // Remove selector-specific configs
  delete config.model_client;
  delete config.selector_prompt;
  delete config.allow_repeated_speaker;

  // Get participant names
  const participantNames = participants
    .map((p) => p.config?.name || p.label)
    .filter(Boolean) as string[];

  // Add handoffs to each participant
  if (config.participants && Array.isArray(config.participants)) {
    config.participants = config.participants.map((participant: any) => {
      const currentName = participant.config?.name || participant.name;
      const otherParticipants = participantNames.filter(
        (name: string) => name !== currentName
      );

      // Deep copy and add handoffs
      const modifiedParticipant = JSON.parse(JSON.stringify(participant));

      if (!modifiedParticipant.config) {
        modifiedParticipant.config = {};
      }

      // Add handoffs as objects with target field
      modifiedParticipant.config.handoffs = otherParticipants.map(
        (name: string) => ({
          target: name,
        })
      );

      return modifiedParticipant;
    });
  }
};

export default configureSwarm;
