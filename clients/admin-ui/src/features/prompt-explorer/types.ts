/**
 * Types for the Prompt Explorer feature.
 *
 * Note: These types are hardcoded until openapi:generate properly generates them.
 * TODO: Replace with generated types from OpenAPI spec when available.
 */

export enum PromptCategory {
  ASSESSMENT = "assessment",
  QUESTIONNAIRE = "questionnaire",
}

export enum PromptType {
  ASSESSMENT_ANALYSIS = "assessment_analysis",
  INTENT_CLASSIFICATION = "intent_classification",
  MESSAGE_GENERATION = "message_generation",
  QUESTION_REPHRASE = "question_rephrase",
  QUESTION_REPHRASE_BATCH = "question_rephrase_batch",
}

export interface PromptInfo {
  id: string;
  name: string;
  description: string;
  category: PromptCategory;
  prompt_type: PromptType;
  template_variables: string[];
  data_sections: string[];
}

export interface DataSection {
  id: string;
  name: string;
}

export interface AssessmentSummary {
  id: string;
  name: string;
  status: string;
  system_fides_key: string | null;
  system_name: string | null;
  template_key: string | null;
  template_name: string | null;
  created_at: string | null;
}

export interface TemplateSummary {
  key: string;
  name: string;
  assessment_type: string;
  authority: string | null;
  region: string | null;
  question_count: number;
}

export interface TemplateQuestion {
  id: string;
  index: number;
  question_text: string;
  section: string | null;
  required: boolean;
}

export interface DataSectionConfig {
  organization: boolean;
  data_categories: boolean;
  data_uses: boolean;
  data_subjects: boolean;
  systems: boolean;
  datasets: boolean;
  policies: boolean;
  privacy_notices: boolean;
  connections: boolean;
}

export interface RenderPromptRequest {
  prompt_type: PromptType;
  data_sections: DataSectionConfig;
  assessment_id?: string;
  declaration_id?: string;
  template_key?: string;
  questionnaire_variables?: Record<string, unknown>;
}

export interface RenderPromptResponse {
  prompt_type: PromptType;
  rendered_prompt: string;
  data_summary: Record<string, unknown>;
  variables_used: Record<string, unknown>;
}

export interface ExecutePromptRequest {
  prompt: string;
  model?: string;
  prompt_type?: PromptType;
}

export interface ExecutePromptResponse {
  model: string;
  response_text: string;
  raw_response: Record<string, unknown>;
}
