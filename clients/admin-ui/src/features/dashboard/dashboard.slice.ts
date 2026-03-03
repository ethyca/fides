import { baseApi } from "~/features/common/api.slice";

type PostureBand = "critical" | "at_risk" | "good" | "excellent";
type DiffDirection = "up" | "down" | "unchanged";

export interface PostureDimension {
  dimension: string;
  label: string;
  weight: number;
  score: number;
  band: PostureBand;
}

export interface PostureResponse {
  score: number;
  diff: number;
  diff_direction: DiffDirection;
  agent_annotation: string;
  dimensions: PostureDimension[];
}

interface ResetResponse {
  message: string;
}

const dashboardApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    resetDashboard: build.mutation<ResetResponse, void>({
      query: () => ({ url: "plus/dashboard/reset", method: "POST" }),
    }),
    getDashboardPosture: build.query<PostureResponse, void>({
      query: () => ({ url: "plus/dashboard/posture" }),
    }),
  }),
});

export const { useResetDashboardMutation, useGetDashboardPostureQuery } =
  dashboardApi;
