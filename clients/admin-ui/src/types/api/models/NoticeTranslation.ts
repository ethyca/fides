/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Notice Translation Schema
 */
export type NoticeTranslation = {
  language: SupportedLanguage;
  title?: string | null;
  description?: string | null;
};
