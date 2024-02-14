/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from './SupportedLanguage';

/**
 * Notice Translation Response Schema
 */
export type NoticeTranslationResponse = {
  language: SupportedLanguage;
  title: string;
  description?: string;
  privacy_notice_history_id: string;
};

