import { Button, Flex } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import ClientSecretModal from "~/features/oauth/ClientSecretModal";
import CreateOAuthClientModal from "~/features/oauth/CreateOAuthClientModal";
import OAuthClientsList from "~/features/oauth/OAuthClientsTable";
import { ScopeRegistryEnum } from "~/types/api";

const ApiClientsPage: NextPage = () => {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [secretModalOpen, setSecretModalOpen] = useState(false);
  const [newClientId, setNewClientId] = useState("");
  const [newClientSecret, setNewClientSecret] = useState("");

  const handleCreated = (clientId: string, secret: string) => {
    setNewClientId(clientId);
    setNewClientSecret(secret);
    setSecretModalOpen(true);
  };

  return (
    <FixedLayout title="API Clients">
      <PageHeader
        heading="API Clients"
        breadcrumbItems={[{ title: "All API clients" }]}
        isSticky={false}
      />
      <Flex justify="flex-end" className="mb-4">
        <Restrict scopes={[ScopeRegistryEnum.CLIENT_CREATE]}>
          <Button
            type="primary"
            onClick={() => setCreateModalOpen(true)}
            data-testid="create-api-client-btn"
          >
            Create API client
          </Button>
        </Restrict>
      </Flex>
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
