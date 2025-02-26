/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Notice Translation Create Schema
 * Makes title non-optional on create
 */
export type NoticeTranslationCreate = {
  language: SupportedLanguage;
  title: string;
  description?: string | null;
};
