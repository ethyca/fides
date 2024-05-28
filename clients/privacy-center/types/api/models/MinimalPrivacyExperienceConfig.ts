/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Minimal representation of a privacy experience config, contains enough information
 * to select experience configs by name in the UI and an ID to link the selections in the database.
 *
 * NOTE: Add to this schema with care. Any fields added to
 * this response schema will be exposed in public-facing
 * (i.e. unauthenticated) API responses. If a field has
 * sensitive information, it should NOT be added to this schema!
 */
export type MinimalPrivacyExperienceConfig = {
  id: string;
  name: string;
};
