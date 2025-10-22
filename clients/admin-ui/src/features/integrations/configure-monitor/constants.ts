import { ClassifyLlmPromptTemplateOptions } from "~/types/api";

export const PROMPT_TEMPLATE_OPTIONS = [
  {
    value: ClassifyLlmPromptTemplateOptions.BASE,
    label: "Base",
  },
  {
    value: ClassifyLlmPromptTemplateOptions.FULL,
    label: "Full",
  },
];
