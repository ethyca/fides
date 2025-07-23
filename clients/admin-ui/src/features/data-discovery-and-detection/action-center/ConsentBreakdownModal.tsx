import {
  AntAlert as Alert,
  AntButton as Button,
  AntFlex as Flex,
  AntModal as Modal,
  AntTable as Table,
  AntTypography as Typography,
} from "fidesui";
import { useMemo, useState } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { PAGE_SIZES } from "~/features/common/table/v2";
import {
  ConsentStatus,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { useGetConsentBreakdownQuery } from "./action-center.slice";

const { Paragraph, Text, Link } = Typography;

interface ConsentBreakdownModalProps {
  isOpen: boolean;
  stagedResource: StagedResourceAPIResponse;
  status: ConsentStatus;
  onCancel: () => void;
  onDownload?: () => void;
}

export const ConsentBreakdownModal = ({
  isOpen,
  stagedResource,
  status,
  onCancel,
  onDownload,
}: ConsentBreakdownModalProps) => {
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0]);

  const { data, isFetching, isError } = useGetConsentBreakdownQuery({
    stagedResourceUrn: stagedResource.urn,
    status,
    page: pageIndex,
    size: pageSize,
  });

  const { items, total: totalRows } = useMemo(
    () =>
      data || {
        items: [],
        total: 0,
        pages: 0,
        filterOptions: { assigned_users: [], systems: [] },
      },
    [data],
  );

  return (
    <Modal
      title="Consent discovery"
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
            View all instances where this asset was detected without consent,
            organized by location and page. Use this to investigate potential
            compliance issues.
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
            columns={[
              {
                title: "Location",
                dataIndex: "location",
                key: "location",
                render: (location: PrivacyNoticeRegion) =>
                  PRIVACY_NOTICE_REGION_RECORD[location] ?? location,
              },
              {
                title: "Page",
                dataIndex: "page",
                key: "page",
                render: (page: string) => (
                  <Link href={page} target="_blank" rel="noopener noreferrer">
                    {page}
                  </Link>
                ),
              },
            ]}
            rowKey={(record) => record.location}
            dataSource={items}
            pagination={
              !!totalRows && (pageIndex > 1 || pageSize > PAGE_SIZES[0])
                ? {
                    current: pageIndex,
                    pageSize,
                    total: totalRows || 0,
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} of ${total} items`,
                    onChange: (page, size) => {
                      setPageIndex(page);
                      if (size !== pageSize) {
                        setPageSize(size);
                        setPageIndex(1);
                      }
                    },
                  }
                : false
            }
            loading={isFetching}
            data-testid="consent-breakdown-modal-table"
          />
        )}
      </Flex>
    </Modal>
  );
};
