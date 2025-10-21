/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassifyLlmPromptTemplateOptions } from "./ClassifyLlmPromptTemplateOptions";

/**
 * Parameters for the llm/classifier/llm_context_classifier function
 */
export type ClassifyLlmParams = {
  llm_model_override?: string | null;
  custom_llm_instructions?: string | null;
  prompt_template?: ClassifyLlmPromptTemplateOptions | null;
  include_rationale?: boolean;
  num_workers?: number;
  taxonomy_instructions?: string | null;
  tagging_instructions?: Record<string, any> | null;
  tagging_instructions_override_all?: Record<string, any> | null;
  tagging_instructions_remove?: Array<string> | null;
};
