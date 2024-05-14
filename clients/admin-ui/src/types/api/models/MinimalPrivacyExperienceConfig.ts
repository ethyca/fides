/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Minimal representation of a privacy experience config, contains enough information
 * to select experience configs by name in the UI and an ID to link the selections in the database.
 */
export type MinimalPrivacyExperienceConfig = {
  id: string;
  name: string;
};
