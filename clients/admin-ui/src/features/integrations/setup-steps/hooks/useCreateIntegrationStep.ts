import { Step } from "./types";

export const useCreateIntegrationStep = (): Step => {
  return {
    title: "Create integration",
    description: "Integration created successfully",
    state: "finish", // If we're viewing the integration, it's already added
  };
};
