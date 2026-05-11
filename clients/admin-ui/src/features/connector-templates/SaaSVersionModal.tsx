import { Button, Flex, Modal, Spin, Tabs, Text } from "fidesui";
import React from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { Editor } from "~/features/common/yaml/helpers";

import {
  useGetConnectorTemplateVersionConfigQuery,
  useGetConnectorTemplateVersionDatasetQuery,
} from "./connector-template.slice";

interface SaaSVersionContentProps {
  connectorType: string;
  version: string;
}

const EDITOR_OPTIONS = {
  readOnly: true,
  minimap: { enabled: false },
  fontSize: 13,
  fontFamily: "Menlo",
  scrollBeyondLastLine: false,
};

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
        <Text type="danger" className="text-sm">
          Could not load version config.
        </Text>
      );
    }
    return (
      <Editor
        defaultLanguage="yaml"
        value={configYaml}
        height="60vh"
        options={EDITOR_OPTIONS}
        theme="light"
      />
    );
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
        <Text type="danger" className="text-sm">
          Could not load dataset for this version.
        </Text>
      );
    }
    if (!datasetYaml) {
      return (
        <Text type="secondary" className="text-sm">
          No dataset available for this version.
        </Text>
      );
    }
    return (
      <Editor
        defaultLanguage="yaml"
        value={datasetYaml}
        height="60vh"
        options={EDITOR_OPTIONS}
        theme="light"
      />
    );
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
