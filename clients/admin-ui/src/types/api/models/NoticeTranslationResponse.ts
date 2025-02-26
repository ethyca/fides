/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Notice Translation Response Schema - adds the historical ID of the notice and translation
 *
 * Privacy preferences against Privacy Notices should be saved against the privacy_notice_history_id
 */
export type NoticeTranslationResponse = {
  language: SupportedLanguage;
  title?: string | null;
  description?: string | null;
  /**
   * The versioned artifact of the translation and its Privacy Notice. Should be supplied when saving privacy preferences.
   */
  privacy_notice_history_id: string;
};
