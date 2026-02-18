import { baseApi } from "~/features/common/api.slice";

// Types
export type PromptCategory = "assessment" | "questionnaire";

export type PromptType =
  | "assessment_analysis"
  | "intent_classification"
  | "message_generation"
  | "question_rephrase"
  | "question_rephrase_batch";

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
}

export interface ExecutePromptResponse {
  model: string;
  response_text: string;
  raw_response: Record<string, unknown>;
}

const promptExplorerApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    // Get all available prompts
    getPrompts: build.query<PromptInfo[], PromptCategory | undefined>({
      query: (category) => ({
        url: "plus/prompt-explorer/prompts",
        params: category ? { category } : undefined,
      }),
    }),

    // Get a specific prompt's info
    getPrompt: build.query<PromptInfo, string>({
      query: (promptId) => `plus/prompt-explorer/prompts/${promptId}`,
    }),

    // Get raw template for a prompt
    getPromptTemplate: build.query<string, string>({
      query: (promptId) => ({
        url: `plus/prompt-explorer/prompts/${promptId}/template`,
        responseHandler: "text",
      }),
    }),

    // Get available data sections
    getDataSections: build.query<DataSection[], void>({
      query: () => "plus/prompt-explorer/data-sections",
    }),

    // Get available assessments for context
    getAssessments: build.query<AssessmentSummary[], void>({
      query: () => "plus/prompt-explorer/assessments",
    }),

    // Get available templates
    getTemplates: build.query<TemplateSummary[], void>({
      query: () => "plus/prompt-explorer/templates",
    }),

    // Get questions from a specific template
    getTemplateQuestions: build.query<TemplateQuestion[], string>({
      query: (templateKey) =>
        `plus/prompt-explorer/templates/${templateKey}/questions`,
    }),

    // Render a prompt with data
    renderPrompt: build.mutation<RenderPromptResponse, RenderPromptRequest>({
      query: (body) => ({
        url: "plus/prompt-explorer/render",
        method: "POST",
        body,
      }),
    }),

    // Execute a prompt against the LLM
    executePrompt: build.mutation<ExecutePromptResponse, ExecutePromptRequest>({
      query: (body) => ({
        url: "plus/prompt-explorer/execute",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const {
  useGetPromptsQuery,
  useGetPromptQuery,
  useGetPromptTemplateQuery,
  useGetDataSectionsQuery,
  useGetAssessmentsQuery,
  useGetTemplatesQuery,
  useGetTemplateQuestionsQuery,
  useRenderPromptMutation,
  useExecutePromptMutation,
} = promptExplorerApi;
