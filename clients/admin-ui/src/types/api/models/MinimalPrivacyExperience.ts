/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Minimal representation of a privacy experience, contains enough information
 * to select experiences by name in the UI and an ID to link the selections in the database.
 */
export type MinimalPrivacyExperience = {
  id: string;
  name: string;
};
