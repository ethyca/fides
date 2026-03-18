import React, { useState } from "react";

import {
  Button,
  ChakraBox as Box,
  ChakraCode as Code,
  ChakraSpinner as Spinner,
  ChakraText as Text,
  Tabs,
} from "fidesui";

import FormModal from "~/features/common/modals/FormModal";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";

import {
  useGetConnectorTemplateVersionConfigQuery,
  useGetConnectorTemplateVersionDatasetQuery,
} from "./connector-template.slice";

interface SaaSVersionContentProps {
  connectorType: string;
  version: string;
}

const SaaSVersionContent = ({
  connectorType,
  version,
}: SaaSVersionContentProps) => {
  const {
    data: configYaml,
    isLoading: configLoading,
    isError: configError,
  } = useGetConnectorTemplateVersionConfigQuery({ connectorType, version });

  const {
    data: datasetYaml,
    isLoading: datasetLoading,
    isError: datasetError,
  } = useGetConnectorTemplateVersionDatasetQuery({ connectorType, version });

  if (configLoading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <Spinner />
      </Box>
    );
  }

  if (configError) {
    return (
      <Text color="red.500" fontSize="sm">
        Could not load version config.
      </Text>
    );
  }

  const tabItems = [
    {
      key: "config",
      label: "Config",
      children: (
        <Code
          display="block"
          whiteSpace="pre"
          overflowX="auto"
          fontSize="xs"
          p={3}
          borderRadius="md"
          backgroundColor="gray.50"
          maxH="60vh"
          overflowY="auto"
        >
          {configYaml}
        </Code>
      ),
    },
    {
      key: "dataset",
      label: "Dataset",
      children: datasetLoading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <Spinner size="sm" />
        </Box>
      ) : datasetError ? (
        <Text color="gray.500" fontSize="sm">
          No dataset available for this version.
        </Text>
      ) : (
        <Code
          display="block"
          whiteSpace="pre"
          overflowX="auto"
          fontSize="xs"
          p={3}
          borderRadius="md"
          backgroundColor="gray.50"
          maxH="60vh"
          overflowY="auto"
        >
          {datasetYaml}
        </Code>
      ),
    },
  ];

  return <Tabs items={tabItems} />;
};

interface SaaSVersionModalProps {
  isOpen: boolean;
  onClose: () => void;
  connectorType: string;
  version: string;
}

const SaaSVersionModal = ({
  isOpen,
  onClose,
  connectorType,
  version,
}: SaaSVersionModalProps) => (
  <FormModal
    title={`${connectorType} — v${version}`}
    isOpen={isOpen}
    onClose={onClose}
    showCloseButton
    size="3xl"
    modalContentProps={{ maxW: "800px" }}
    footer={
      <Button onClick={onClose} data-testid="version-modal-close-btn">
        Close
      </Button>
    }
  >
    <SaaSVersionContent connectorType={connectorType} version={version} />
  </FormModal>
);

interface PendingModalState {
  connectionKey: string;
  version: string;
}

interface ActiveModalState {
  connectorType: string;
  version: string;
}

/**
 * Hook providing a version detail modal keyed by connection key + version string.
 * Resolves connector_type via the connection config before opening the modal.
 */
export const useSaaSVersionModal = () => {
  const [pending, setPending] = useState<PendingModalState | null>(null);
  const [active, setActive] = useState<ActiveModalState | null>(null);

  const { data: connection } = useGetDatastoreConnectionByKeyQuery(
    pending?.connectionKey ?? "",
    { skip: !pending?.connectionKey },
  );

  // Once the connection resolves, promote pending to active so the modal opens.
  // connectorType is captured into active so the modal doesn't depend on the
  // query after pending is cleared (skip: true returns undefined data).
  // If the connection has no saas_config.type (non-SaaS), bail out silently
  // so pending doesn't stay set indefinitely.
  React.useEffect(() => {
    if (!pending || !connection) return;
    if (connection.saas_config?.type) {
      setActive({ connectorType: connection.saas_config.type, version: pending.version });
    }
    setPending(null);
  }, [pending, connection]);

  const openVersionModal = (connectionKey: string, version: string) => {
    setPending({ connectionKey, version });
  };

  const handleClose = () => setActive(null);

  const modal = active ? (
    <SaaSVersionModal
      isOpen
      onClose={handleClose}
      connectorType={active.connectorType}
      version={active.version}
    />
  ) : null;

  return { openVersionModal, modal };
};

export default SaaSVersionModal;
