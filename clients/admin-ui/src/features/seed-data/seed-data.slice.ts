import { baseApi } from "~/features/common/api.slice";

export interface SeedTasksConfig {
  sample_resources?: boolean;
  messaging_mailgun?: boolean;
  storage_s3?: boolean;
  linked_connections?: boolean;
  consent_notices?: boolean;
  consent_experiences?: boolean;
  compass_vendors?: boolean;
  email_templates?: boolean;
  chat_slack?: boolean;
  privacy_assessments?: boolean;
  consent_preferences?: boolean;
  discovery_monitors?: boolean;
  pbac?: boolean;
  dashboard?: boolean;
  disclosure_metrics?: boolean;
}

export interface SeedProfileDetail {
  name: string;
  tasks: SeedTasksConfig;
}

export interface SeedRequest {
  secret_profile?: string;
  tasks: SeedTasksConfig;
}

export interface SeedResponse {
  execution_id: string;
  message: string;
}

export interface SeedStepStatus {
  status: "pending" | "in_progress" | "complete" | "skipped" | "error";
  message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface SeedStatusResponse {
  id: string;
  status: "pending" | "in_progress" | "complete" | "error";
  started_at: string;
  completed_at?: string;
  steps: Record<string, SeedStepStatus>;
  error?: string;
}

const seedDataApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listSeedProfiles: build.query<string[], void>({
      query: () => ({
        url: "plus/seed/profiles",
      }),
    }),
    getSeedProfile: build.query<SeedProfileDetail, string>({
      query: (profileName) => ({
        url: `plus/seed/profiles/${profileName}`,
      }),
    }),
    triggerSeed: build.mutation<SeedResponse, SeedRequest>({
      query: (body) => ({
        url: "plus/seed",
        method: "POST",
        body,
      }),
      // Invalidate all potentially affected tags so cached data refreshes
      // after the user navigates to the seeded pages.
      invalidatesTags: [
        "DataPurpose",
        "DataConsumer",
        "QueryLogConfig",
        "Datastore Connection",
        "Dataset",
        "Datasets",
        "System",
        "Policies",
        "Privacy Notices",
        "Privacy Experience Configs",
        "Dictionary",
        "System Vendors",
        "Messaging Templates",
        "Discovery Monitor Configs",
        "Messaging Config",
        "Configuration Settings",
        "Request",
        "Fides Dashboard",
      ],
    }),
    getSeedStatus: build.query<SeedStatusResponse, string>({
      query: (executionId) => ({
        url: `plus/seed/status/${executionId}`,
      }),
    }),
    getLatestSeedStatus: build.query<SeedStatusResponse | null, void>({
      query: () => ({
        url: "plus/seed/status",
      }),
    }),
  }),
});

export const {
  useListSeedProfilesQuery,
  useGetSeedProfileQuery,
  useTriggerSeedMutation,
  useGetSeedStatusQuery,
  useGetLatestSeedStatusQuery,
} = seedDataApi;
