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
  discovery_monitors?: boolean;
  pbac?: boolean;
  dashboard?: boolean;
}

export interface SeedRequest {
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

/**
 * Cache tags to invalidate when seeding completes.
 * Maps each seed task to the tags it affects.
 */
const SEED_TASK_INVALIDATION_TAGS: Record<keyof SeedTasksConfig, string[]> = {
  pbac: [
    "DataPurpose",
    "DataConsumer",
    "QueryLogConfig",
    "Datastore Connection",
    "Dataset",
    "Datasets",
  ],
  sample_resources: ["System", "Dataset", "Datasets", "Policies"],
  linked_connections: ["Datastore Connection"],
  consent_notices: ["Privacy Notices"],
  consent_experiences: ["Privacy Experience Configs"],
  compass_vendors: ["System", "Dictionary", "System Vendors"],
  email_templates: ["Messaging Templates"],
  discovery_monitors: ["Discovery Monitor Configs", "Datastore Connection"],
  messaging_mailgun: ["Messaging Config"],
  storage_s3: ["Configuration Settings"],
  dashboard: [
    "System",
    "Privacy Requests",
    "Fides Dashboard",
  ],
};

const seedDataApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    triggerSeed: build.mutation<SeedResponse, SeedRequest>({
      query: (body) => ({
        url: "plus/seed",
        method: "POST",
        body,
      }),
      // Invalidate tags for all enabled tasks so cached data refreshes
      // after the user navigates to the seeded pages.
      invalidatesTags: (_result, _error, arg) => {
        const tags: string[] = [];
        const { tasks } = arg;
        (Object.keys(tasks) as (keyof SeedTasksConfig)[]).forEach((key) => {
          if (tasks[key] && SEED_TASK_INVALIDATION_TAGS[key]) {
            tags.push(...SEED_TASK_INVALIDATION_TAGS[key]);
          }
        });
        // Deduplicate
        return [...new Set(tags)];
      },
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
  useTriggerSeedMutation,
  useGetSeedStatusQuery,
  useGetLatestSeedStatusQuery,
} = seedDataApi;
