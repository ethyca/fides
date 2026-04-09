import { Button, Flex, Modal, Spin, Tabs, Text } from "fidesui";
import React from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";

import {
  useGetConnectorTemplateVersionConfigQuery,
  useGetConnectorTemplateVersionDatasetQuery,
} from "./connector-template.slice";

interface SaaSVersionContentProps {
  connectorType: string;
  version: string;
}

const YamlBlock = ({ yaml }: { yaml: string | undefined }) => (
  <pre className="max-h-[60vh] overflow-auto whitespace-pre rounded-md bg-gray-50 p-3 text-xs">
    {yaml}
  </pre>
);

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

  const renderConfig = () => {
    if (configLoading) {
      return (
        <Flex justify="center" className="py-8">
          <Spin />
        </Flex>
      );
    }
    if (configError) {
      return (
        <Text className="text-sm text-red-500">
          Could not load version config.
        </Text>
      );
    }
    return <YamlBlock yaml={configYaml} />;
  };

  const renderDataset = () => {
    if (datasetLoading) {
      return (
        <Flex justify="center" className="py-4">
          <Spin size="small" />
        </Flex>
      );
    }
    if (datasetError) {
      return (
        <Text className="text-sm text-red-500">
          Could not load dataset for this version.
        </Text>
      );
    }
    if (!datasetYaml) {
      return (
        <Text className="text-sm text-gray-500">
           No dataset available for this version.
        </Text>
      );
    }
    return <YamlBlock yaml={datasetYaml} />;
  };

  const tabItems = [
    { key: "config", label: "Config", children: renderConfig() },
    { key: "dataset", label: "Dataset", children: renderDataset() },
  ];

  return <Tabs items={tabItems} />;
};

export interface SaaSVersionModalProps {
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
  <Modal
    open={isOpen}
    onCancel={onClose}
    width={MODAL_SIZE.xl}
    centered
    destroyOnHidden
    title={`${connectorType} — v${version}`}
    footer={
      <Flex justify="flex-end">
        <Button onClick={onClose} data-testid="version-modal-close-btn">
          Close
        </Button>
      </Flex>
    }
  >
    <SaaSVersionContent connectorType={connectorType} version={version} />
  </Modal>
);

export default SaaSVersionModal;
