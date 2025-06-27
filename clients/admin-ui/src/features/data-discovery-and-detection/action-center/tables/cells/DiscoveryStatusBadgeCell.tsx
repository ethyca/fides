import {
  AntButton as Button,
  AntModal as Modal,
  AntTable as Table,
  AntTag as Tag,
  AntTooltip as Tooltip,
} from "fidesui";
import { useState } from "react";

import { formatDate } from "~/features/common/utils";
import { AggregatedConsent } from "~/types/api";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: AggregatedConsent;
  dateDiscovered: string | null | undefined;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
  dateDiscovered,
}: DiscoveryStatusBadgeCellProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const handleClick = () => {
    setIsOpen(true);
  };
  const handleCancel = () => {
    setIsOpen(false);
  };
  const handleDownload = () => {
    console.log("download");
  };
  return (
    <>
      <Tooltip title={dateDiscovered ? formatDate(dateDiscovered) : undefined}>
        {/* tooltip throws errors if immediate child is not available or changes after render so this div wrapper helps keep it stable */}
        {consentAggregated === AggregatedConsent.WITHOUT_CONSENT && (
          <Tag color="error" onClick={handleClick}>
            Without consent
          </Tag>
        )}
        {consentAggregated === AggregatedConsent.WITH_CONSENT && (
          <Tag color="success">With consent</Tag>
        )}
        {consentAggregated === AggregatedConsent.EXEMPT && (
          <Tag>Consent exempt</Tag>
        )}
        {consentAggregated === AggregatedConsent.UNKNOWN && <Tag>Unknown</Tag>}
      </Tooltip>
      {isOpen && (
        <Modal // TASK: convert to component and add API call
          title="Consent discovery"
          width={768}
          open={isOpen}
          onCancel={() => setIsOpen(false)}
          footer={[
            <Button key="cancel" onClick={handleCancel}>
              Cancel
            </Button>,
            <Button key="download" type="primary" onClick={handleDownload}>
              Download
            </Button>,
          ]}
        >
          <p className="mb-4">
            View all instances where this asset was detected without consent,
            organized by location and page. Use this to investigate potential
            compliance issues.
          </p>
          {/* TASK: add table data from API */}
          <Table
            columns={[
              {
                title: "Location",
                dataIndex: "location",
                key: "location",
              },
              {
                title: "Page",
                dataIndex: "page",
                key: "page",
              },
            ]}
            dataSource={[
              {
                key: "1",
                location: "United States",
                page: ".ethyca.com/home",
              },
            ]}
            pagination={false}
          />
        </Modal>
      )}
    </>
  );
};
