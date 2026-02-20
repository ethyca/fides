import { baseApi } from "~/features/common/api.slice";

import type {
  AssessmentSummary,
  DataSection,
  DataSectionConfig,
  ExecutePromptRequest,
  ExecutePromptResponse,
  PromptCategory,
  PromptInfo,
  PromptType,
  RenderPromptRequest,
  RenderPromptResponse,
  TemplateQuestion,
  TemplateSummary,
} from "./types";

// Re-export types for convenience
export type {
  AssessmentSummary,
  DataSection,
  DataSectionConfig,
  ExecutePromptRequest,
  ExecutePromptResponse,
  PromptCategory,
  PromptInfo,
  PromptType,
  RenderPromptRequest,
  RenderPromptResponse,
  TemplateQuestion,
  TemplateSummary,
};

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
