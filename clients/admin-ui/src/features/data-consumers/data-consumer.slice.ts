import { baseApi } from "~/features/common/api.slice";

export interface DataConsumer {
  id: string;
  name: string;
  type: string;
  scope?: Record<string, string>;
  contact_email?: string;
  description?: string;
  tags?: string[];
  purpose_fides_keys?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface ConsumerTypeDefinition {
  key: string;
  name: string;
  description: string;
  platform: string;
  platform_label: string;
  supports_members: boolean;
  scope_keys: Record<string, string>;
  display_key: string;
}

export interface AvailableScope {
  type: string;
  scope: Record<string, string>;
  display_name: string;
}

interface DataConsumerParams {
  page?: number;
  size?: number;
  search?: string;
  type?: string;
  purpose_fides_key?: string;
}

interface PaginatedDataConsumers {
  items: DataConsumer[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

type CreateDataConsumerPayload = Omit<
  DataConsumer,
  "id" | "created_at" | "updated_at"
>;

type UpdateDataConsumerPayload = {
  id: string;
} & Partial<Omit<DataConsumer, "id" | "created_at" | "updated_at">>;

interface AssignConsumerPurposesPayload {
  id: string;
  purposeFidesKeys: string[];
}

export const dataConsumerApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAllDataConsumers: builder.query<
      PaginatedDataConsumers,
      DataConsumerParams
    >({
      query: (params) => ({
        url: `data-consumer`,
        params,
      }),
      providesTags: ["DataConsumer"],
    }),
    getDataConsumerById: builder.query<DataConsumer, string>({
      query: (id) => ({
        url: `data-consumer/${id}`,
      }),
      providesTags: ["DataConsumer"],
    }),
    createDataConsumer: builder.mutation<
      DataConsumer,
      CreateDataConsumerPayload
    >({
      query: (body) => ({
        url: `data-consumer`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["DataConsumer"],
    }),
    updateDataConsumer: builder.mutation<
      DataConsumer,
      UpdateDataConsumerPayload
    >({
      query: ({ id, ...body }) => ({
        url: `data-consumer/${id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["DataConsumer"],
    }),
    deleteDataConsumer: builder.mutation<void, string>({
      query: (id) => ({
        url: `data-consumer/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["DataConsumer"],
    }),
    assignConsumerPurposes: builder.mutation<
      DataConsumer,
      AssignConsumerPurposesPayload
    >({
      query: ({ id, purposeFidesKeys }) => ({
        url: `data-consumer/${id}/purpose`,
        method: "PUT",
        body: { purpose_fides_keys: purposeFidesKeys },
      }),
      invalidatesTags: ["DataConsumer"],
    }),
    getConsumerTypes: builder.query<ConsumerTypeDefinition[], void>({
      query: () => ({
        url: `plus/pbac/consumer-types`,
      }),
    }),
    getAvailableScopes: builder.query<AvailableScope[], void>({
      query: () => ({
        url: `plus/pbac/available-scopes`,
      }),
      providesTags: ["DataConsumer"],
    }),
  }),
});

export const {
  useGetAllDataConsumersQuery,
  useGetDataConsumerByIdQuery,
  useCreateDataConsumerMutation,
  useUpdateDataConsumerMutation,
  useDeleteDataConsumerMutation,
  useAssignConsumerPurposesMutation,
  useGetConsumerTypesQuery,
  useGetAvailableScopesQuery,
} = dataConsumerApi;
