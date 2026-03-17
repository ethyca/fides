import {
  Alert,
  Button,
  Flex,
  Modal,
  Tabs,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { API_CLIENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import ClientSecretModal from "~/features/oauth/ClientSecretModal";
import {
  useGetOAuthClientQuery,
  useRotateOAuthClientSecretMutation,
} from "~/features/oauth/oauth-clients.slice";
import OAuthClientForm from "~/features/oauth/OAuthClientForm";
import { ScopeRegistryEnum } from "~/types/api";

const SecretManagementTab = ({ clientId }: { clientId: string }) => {
  const message = useMessage();
  const [secretModalOpen, setSecretModalOpen] = useState(false);
  const [rotatedSecret, setRotatedSecret] = useState("");
  const [rotateSecret, { isLoading }] = useRotateOAuthClientSecretMutation();

  const handleRotate = async () => {
    const result = await rotateSecret(clientId);
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else if (result.data) {
      setRotatedSecret(result.data.client_secret);
      setSecretModalOpen(true);
    }
  };

  const confirmRotate = () => {
    Modal.confirm({
      title: "Rotate client secret?",
      content:
        "The current secret will be immediately invalidated. Any integrations using this client will need to be updated with the new secret.",
      okText: "Rotate secret",
      okButtonProps: { danger: true },
      onOk: handleRotate,
    });
  };

  return (
    <>
      <div
        className="flex max-w-lg flex-col gap-3"
        data-testid="secret-management-tab"
      >
        <p className="font-medium">Rotate secret</p>
        <p className="text-sm text-gray-600">
          Rotating the secret immediately invalidates the current one. Any
          integrations using this client will need to be updated with the new
          secret.
        </p>
        <div>
          <Button
            danger
            onClick={confirmRotate}
            loading={isLoading}
            data-testid="rotate-secret-btn"
          >
            Rotate secret
          </Button>
        </div>
      </div>
      <ClientSecretModal
        clientId={clientId}
        secret={rotatedSecret}
        context="rotated"
        isOpen={secretModalOpen}
        onClose={() => setSecretModalOpen(false)}
      />
    </>
  );
};

const ApiClientDetailPage: NextPage = () => {
  const router = useRouter();
  const clientId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : (router.query.id ?? "");

  const {
    data: client,
    isLoading,
    error,
  } = useGetOAuthClientQuery(clientId, {
    skip: !clientId,
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching this API client"
        actions={[
          {
            label: "Return to API clients",
            onClick: () => router.push(API_CLIENTS_ROUTE),
          },
        ]}
      />
    );
  }

  const tabItems = client
    ? [
        {
          key: "details",
          label: "Details",
          children: (
            <Restrict scopes={[ScopeRegistryEnum.CLIENT_UPDATE]}>
              <OAuthClientForm
                client={client}
                onClose={() => router.push(API_CLIENTS_ROUTE)}
              />
            </Restrict>
          ),
        },
        {
          key: "secret",
          label: "Secret management",
          children: (
            <Restrict scopes={[ScopeRegistryEnum.CLIENT_UPDATE]}>
              <SecretManagementTab clientId={client.client_id} />
            </Restrict>
          ),
        },
      ]
    : [];

  return (
    <FixedLayout title="API Clients - Edit">
      <PageHeader
        heading={client?.name ?? "API client"}
        breadcrumbItems={[
          { title: "All API clients", href: API_CLIENTS_ROUTE },
          { title: client?.name ?? clientId },
        ]}
        isSticky={false}
      />
      {client && (
        <Flex align="center" gap={4} className="-mt-2 mb-4">
          <Typography.Text type="secondary" className="font-mono text-xs">
            {client.client_id}
          </Typography.Text>
          <ClipboardButton
            copyText={client.client_id}
            size="small"
            data-testid="copy-client-id-btn"
          />
        </Flex>
      )}
      {isLoading && (
        <Flex justify="center" align="center" className="h-32">
          <div className="size-8 animate-spin rounded-full border-b-2 border-gray-900" />
        </Flex>
      )}
      {!isLoading && !client && (
        <Alert message="API client not found." type="warning" showIcon />
      )}
      {client && <Tabs items={tabItems} className="w-full" />}
    </FixedLayout>
  );
};

export default ApiClientDetailPage;
