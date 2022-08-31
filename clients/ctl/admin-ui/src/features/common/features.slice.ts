import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

interface HealthResponse {
  core_fidesctl_version: string;
  status: "healthy";
}

export const plusApi = createApi({
  reducerPath: "plusApi",
  baseQuery: fetchBaseQuery({
    baseUrl: `${process.env.NEXT_PUBLIC_FIDESCTL_API}/plus`,
  }),
  tagTypes: ["Plus"],
  endpoints: (build) => ({
    getHealth: build.query<HealthResponse, void>({
      query: () => "health",
    }),
  }),
});

const { useGetHealthQuery } = plusApi;

export interface Features {
  plus: boolean;
}

export const useFeatures = (): Features => {
  const { isSuccess } = useGetHealthQuery();

  return {
    plus: isSuccess,
  };
};
