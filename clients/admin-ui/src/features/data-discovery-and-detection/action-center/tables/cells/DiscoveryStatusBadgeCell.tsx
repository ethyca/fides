import {
  AntButton as Button,
  AntModal as Modal,
  AntTable as Table,
  AntTag as Tag,
  AntTooltip as Tooltip,
  Icons,
} from "fidesui";
import { useState } from "react";

import { AggregatedConsent } from "~/types/api";

interface DiscoveryStatusBadgeCellProps {
  consentAggregated: AggregatedConsent;
}

export const DiscoveryStatusBadgeCell = ({
  consentAggregated,
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
      {consentAggregated === AggregatedConsent.WITHOUT_CONSENT && (
        <Tooltip title="Asset was detected before the user gave consent or without any consent. Click the info icon for more details.">
          <Tag
            color="error"
            closeIcon={<Icons.Information style={{ width: 12, height: 12 }} />}
            closeButtonLabel="View details"
            onClose={handleClick}
          >
            Without consent
          </Tag>
        </Tooltip>
      )}
      {consentAggregated === AggregatedConsent.WITH_CONSENT && (
        <Tooltip title="Asset was detected after the user gave consent">
          <Tag color="success">With consent</Tag>
        </Tooltip>
      )}
      {consentAggregated === AggregatedConsent.EXEMPT && (
        <Tooltip title="Asset is valid regardless of consent">
          <Tag>Consent exempt</Tag>
        </Tooltip>
      )}
      {consentAggregated === AggregatedConsent.UNKNOWN && (
        <Tooltip title="Did not find consent information for this asset. You may need to re-run the monitor.">
          <Tag>Unknown</Tag>
        </Tooltip>
      )}
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
