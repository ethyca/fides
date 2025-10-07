import {
  AntAlert as Alert,
  AntButton as Button,
  AntFlex as Flex,
  AntModal as Modal,
  AntTable as Table,
  AntTypography as Typography,
} from "fidesui";

import { StagedResourceAPIResponse } from "~/types/api";

import { useConsentBreakdownTable } from "./hooks/useConsentBreakdownTable";

const { Paragraph, Text } = Typography;

interface ConsentBreakdownModalProps {
  isOpen: boolean;
  stagedResource: StagedResourceAPIResponse;
  onCancel: () => void;
  onDownload?: () => void;
}

export const ConsentBreakdownModal = ({
  isOpen,
  stagedResource,
  onCancel,
  onDownload,
}: ConsentBreakdownModalProps) => {
  const { columns, tableProps, isError } = useConsentBreakdownTable({
    stagedResource,
  });

  return (
    <Modal
      title="Compliance issues"
      width={768}
      open={isOpen}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        !!onDownload && (
          <Button key="download" type="primary" onClick={onDownload}>
            Download
          </Button>
        ),
      ]}
      data-testid="consent-breakdown-modal"
    >
      <Flex
        vertical
        className="gap-6"
        data-testid="consent-breakdown-modal-content"
      >
        <div>
          <Paragraph>
            View all instances where this asset was detected with consent
            compliance issues, organized by location and page. This includes
            assets loaded without consent, before consent, or when CMP failed.
          </Paragraph>
          <Paragraph>
            <Text strong>Asset name:</Text>{" "}
            {stagedResource.name ?? <Text italic>Unknown</Text>},{" "}
            <Text strong>System:</Text>{" "}
            {stagedResource.system ?? <Text italic>Unassigned</Text>},{" "}
            <Text strong>Domain:</Text>{" "}
            {stagedResource.domain ?? <Text italic>Unknown</Text>}
          </Paragraph>
        </div>
        {isError ? (
          <Alert
            type="error"
            message="Error fetching data"
            description="Please try again later."
            showIcon
          />
        ) : (
          <Table
            {...tableProps}
            columns={columns}
            data-testid="consent-breakdown-modal-table"
            tableLayout="fixed"
            scroll={{ scrollToFirstRowOnChange: true }}
          />
        )}
      </Flex>
    </Modal>
  );
};
