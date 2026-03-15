import { baseApi } from "~/features/common/api.slice";
import {
  Page_PreApprovalWebhookResponse_,
  PreApprovalWebhookCreate,
  PreApprovalWebhookResponse,
} from "~/types/api";

const PRE_APPROVAL_WEBHOOK_ROUTE = "/dsr/webhook/pre_approval";

const preApprovalWebhooksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPreApprovalWebhooks: build.query<
      Page_PreApprovalWebhookResponse_,
      void
    >({
      query: () => ({
        url: PRE_APPROVAL_WEBHOOK_ROUTE,
      }),
      providesTags: ["Pre-Approval Webhooks"],
    }),
    createOrUpdatePreApprovalWebhooks: build.mutation<
      PreApprovalWebhookResponse[],
      PreApprovalWebhookCreate[]
    >({
      query: (webhooks) => ({
        url: PRE_APPROVAL_WEBHOOK_ROUTE,
        method: "PUT",
        body: webhooks,
      }),
      invalidatesTags: ["Pre-Approval Webhooks"],
    }),
    deletePreApprovalWebhook: build.mutation<void, string>({
      query: (webhookKey) => ({
        url: `${PRE_APPROVAL_WEBHOOK_ROUTE}/${webhookKey}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Pre-Approval Webhooks"],
    }),
  }),
});

export const {
  useGetPreApprovalWebhooksQuery,
  useCreateOrUpdatePreApprovalWebhooksMutation,
  useDeletePreApprovalWebhookMutation,
} = preApprovalWebhooksApi;
