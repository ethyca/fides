import { CONNECTION_ROUTE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";
import {
  Page_PreApprovalWebhookResponse_,
  PreApprovalWebhookCreate,
  PreApprovalWebhookResponse,
} from "~/types/api";

const PRE_APPROVAL_WEBHOOK_ROUTE = "/dsr/webhook/pre_approval";

/**
 * Shape returned by GET /connection/{key}, which includes secrets
 * with sensitive fields redacted (e.g. authorization → "**********").
 */
interface ConnectionConfigWithSecrets {
  key: string;
  name: string | null;
  connection_type: string;
  secrets?: Record<string, string> | null;
  [key: string]: unknown;
}

const preApprovalWebhooksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPreApprovalWebhooks: build.query<Page_PreApprovalWebhookResponse_, void>(
      {
        query: () => ({
          url: PRE_APPROVAL_WEBHOOK_ROUTE,
        }),
        providesTags: ["Pre-Approval Webhooks"],
      },
    ),
    getConnectionConfigByKey: build.query<ConnectionConfigWithSecrets, string>({
      query: (connectionKey) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}`,
      }),
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
    createConnectionConfigForWebhook: build.mutation<
      unknown,
      {
        key: string;
        name: string;
        connection_type: string;
        access: string;
      }
    >({
      query: (params) => ({
        url: CONNECTION_ROUTE,
        method: "PATCH",
        body: [params],
      }),
    }),
    patchConnectionSecretsForWebhook: build.mutation<
      unknown,
      { connectionKey: string; secrets: Record<string, string> }
    >({
      query: ({ connectionKey, secrets }) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}/secret?verify=false`,
        method: "PATCH",
        body: secrets,
      }),
    }),
  }),
});

export const {
  useGetPreApprovalWebhooksQuery,
  useGetConnectionConfigByKeyQuery,
  useLazyGetConnectionConfigByKeyQuery,
  useCreateOrUpdatePreApprovalWebhooksMutation,
  useDeletePreApprovalWebhookMutation,
  useCreateConnectionConfigForWebhookMutation,
  usePatchConnectionSecretsForWebhookMutation,
} = preApprovalWebhooksApi;
