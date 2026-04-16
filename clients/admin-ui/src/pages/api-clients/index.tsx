import { Button, Flex, Tooltip } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import ClientSecretModal from "~/features/oauth/ClientSecretModal";
import CreateOAuthClientModal from "~/features/oauth/CreateOAuthClientModal";
import OAuthClientsList from "~/features/oauth/OAuthClientsList";
import { ScopeRegistryEnum } from "~/types/api";

const ApiClientsPage: NextPage = () => {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [secretModalOpen, setSecretModalOpen] = useState(false);
  const [newClientId, setNewClientId] = useState("");
  const [newClientSecret, setNewClientSecret] = useState("");

  const canCreate = useHasPermission([ScopeRegistryEnum.CLIENT_CREATE]);

  const handleCreated = (clientId: string, secret: string) => {
    setNewClientId(clientId);
    setNewClientSecret(secret);
    setCreateModalOpen(false);
    setSecretModalOpen(true);
  };

  return (
    <FixedLayout title="API Clients">
      <PageHeader
        heading="API Clients"
        breadcrumbItems={[{ title: "All API clients" }]}
        isSticky={false}
        rightContent={
          <Tooltip
            title={
              !canCreate
                ? "You don't have permission to create API clients."
                : undefined
            }
          >
            {/* Disabled buttons swallow mouse events, preventing the tooltip from firing */}
            <span>
              <Button
                type="primary"
                disabled={!canCreate}
                onClick={() => setCreateModalOpen(true)}
                data-testid="create-api-client-btn"
              >
                Create API client
              </Button>
            </span>
          </Tooltip>
        }
      />
      <OAuthClientsList />
      <CreateOAuthClientModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={handleCreated}
      />
      <ClientSecretModal
        clientId={newClientId}
        secret={newClientSecret}
        context="created"
        isOpen={secretModalOpen}
        onClose={() => setSecretModalOpen(false)}
      />
    </FixedLayout>
  );
};

export default ApiClientsPage;
