import {
  Alert,
  Button,
  ChakraDivider as Divider,
  ChakraSpinner as Spinner,
  ChakraStack as Stack,
  ChakraText as Text,
  Flex,
  useChakraDisclosure as useDisclosure,
  useChakraToast as useToast,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { API_CLIENTS_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { errorToastParams } from "~/features/common/toast";
import ClientSecretModal from "~/features/oauth/ClientSecretModal";
import OAuthClientForm from "~/features/oauth/OAuthClientForm";
import {
  useGetOAuthClientQuery,
  useRotateOAuthClientSecretMutation,
} from "~/features/oauth/oauth-clients.slice";
import { ScopeRegistryEnum } from "~/types/api";

const RotateSecretSection = ({ clientId }: { clientId: string }) => {
  const toast = useToast();
  const secretModal = useDisclosure();
  const [rotatedSecret, setRotatedSecret] = useState("");
  const [rotateSecret, { isLoading }] = useRotateOAuthClientSecretMutation();

  const handleRotate = async () => {
    const result = await rotateSecret(clientId);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else if (result.data) {
      setRotatedSecret(result.data.client_secret);
      secretModal.onOpen();
    }
  };

  return (
    <>
      <Stack spacing={2}>
        <Text fontWeight="medium">Client secret</Text>
        <Text fontSize="sm" color="gray.600">
          Rotating the secret immediately invalidates the current one. Any
          integrations using this client will need to be updated.
        </Text>
        <div>
          <Button
            onClick={handleRotate}
            loading={isLoading}
            data-testid="rotate-secret-btn"
          >
            Rotate secret
          </Button>
        </div>
      </Stack>
      <ClientSecretModal
        clientId={clientId}
        secret={rotatedSecret}
        context="rotated"
        {...secretModal}
      />
    </>
  );
};

const ApiClientDetailPage: NextPage = () => {
  const router = useRouter();
  const clientId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : router.query.id ?? "";

  const { data: client, isLoading, error } = useGetOAuthClientQuery(clientId, {
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
      {isLoading && (
        <Flex justify="center" align="center" className="h-32">
          <Spinner color="primary.900" />
        </Flex>
      )}
      {!isLoading && !client && (
        <Alert
          message="API client not found."
          type="warning"
          showIcon
        />
      )}
      {client && (
        <Stack spacing={8} maxW="2xl">
          <Restrict scopes={[ScopeRegistryEnum.CLIENT_UPDATE]}>
            <OAuthClientForm
              client={client}
              onClose={() => router.push(API_CLIENTS_ROUTE)}
            />
          </Restrict>
          <Divider />
          <Restrict scopes={[ScopeRegistryEnum.CLIENT_UPDATE]}>
            <RotateSecretSection clientId={client.client_id} />
          </Restrict>
        </Stack>
      )}
    </FixedLayout>
  );
};

export default ApiClientDetailPage;
