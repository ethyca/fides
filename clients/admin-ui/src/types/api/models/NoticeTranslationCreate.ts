/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from './SupportedLanguage';

/**
 * Notice Translation Schema
 */
export type NoticeTranslationCreate = {
  language: SupportedLanguage;
  title: string;
  description?: string;
};

