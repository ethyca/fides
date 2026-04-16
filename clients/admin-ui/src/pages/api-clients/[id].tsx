import {
  Alert,
  Button,
  Flex,
  Modal,
  Paragraph,
  Spin,
  Tabs,
  Tooltip,
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
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import ClientSecretModal from "~/features/oauth/ClientSecretModal";
import {
  useDeleteOAuthClientMutation,
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
  const canUpdate = useHasPermission([ScopeRegistryEnum.CLIENT_UPDATE]);

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
      <Flex
        gap="middle"
        className="max-w-lg"
        vertical
        data-testid="secret-management-tab"
      >
        <Paragraph>Rotate secret</Paragraph>
        <Paragraph type="secondary" className="text-sm">
          Rotating the secret immediately invalidates the current one. Any
          integrations using this client will need to be updated with the new
          secret.
        </Paragraph>

        <Tooltip
          title={
            !canUpdate
              ? "You don't have permission to update API clients."
              : undefined
          }
        >
          <span>
            <Button
              disabled={!canUpdate}
              danger
              onClick={confirmRotate}
              loading={isLoading}
              data-testid="rotate-secret-btn"
            >
              Rotate secret
            </Button>
          </span>
        </Tooltip>
      </Flex>
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
  const message = useMessage();
  const clientId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : (router.query.id ?? "");
  const [deleteClient, { isLoading: isDeleting }] =
    useDeleteOAuthClientMutation();

  const {
    data: client,
    isLoading,
    error,
  } = useGetOAuthClientQuery(clientId, {
    skip: !router.isReady || !clientId,
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
            <OAuthClientForm
              client={client}
              onClose={() => router.push(API_CLIENTS_ROUTE)}
            />
          ),
        },
        {
          key: "secret",
          label: "Secret management",
          children: <SecretManagementTab clientId={client.client_id} />,
        },
      ]
    : [];

  const confirmDelete = () => {
    Modal.confirm({
      title: "Delete API client?",
      content:
        "This client will be permanently deleted. Any integrations using it will stop working immediately.",
      okText: "Delete client",
      okButtonProps: { danger: true },
      onOk: async () => {
        const result = await deleteClient(clientId);
        if (isErrorResult(result)) {
          message.error(getErrorMessage(result.error));
        } else {
          router.push(API_CLIENTS_ROUTE);
        }
      },
    });
  };

  return (
    <FixedLayout title="API Clients - Edit">
      <PageHeader
        heading={client?.name ?? "API client"}
        breadcrumbItems={[
          { title: "All API clients", href: API_CLIENTS_ROUTE },
          { title: client?.name ?? clientId },
        ]}
        isSticky={false}
        rightContent={
          client && (
            <Restrict scopes={[ScopeRegistryEnum.CLIENT_DELETE]}>
              <Button
                danger
                onClick={confirmDelete}
                loading={isDeleting}
                data-testid="delete-client-btn"
              >
                Delete client
              </Button>
            </Restrict>
          )
        }
      />
      {client && (
        <Flex align="center" gap={4} className="-mt-2 mb-4">
          <Typography.Text
            type="secondary"
            className="font-mono text-xs"
            copyable
          >
            {client.client_id}
          </Typography.Text>
        </Flex>
      )}
      {isLoading && (
        <Flex justify="center" align="center" className="h-32">
          <Spin />
        </Flex>
      )}
      {!isLoading && !client && (
        <Alert title="API client not found." type="warning" showIcon />
      )}
      {client && <Tabs items={tabItems} className="w-full" />}
    </FixedLayout>
  );
};

export default ApiClientDetailPage;
