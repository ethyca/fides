import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import type { PrivacyNoticeResponse } from "~/types/api";

import PreviewCard from "./PreviewCard";

interface ExperienceConfigSectionProps {
  region: string;
  onRegionChange: (region: string) => void;
  propertyId: string;
  onPropertyIdChange: (propertyId: string) => void;
  onFetchExperience: () => void;
  isLoading: boolean;
  errorMessage: string;
  privacyNotices: PrivacyNoticeResponse[];
}

/**
 * Renders a list of privacy notices with their children
 */
const PrivacyNoticesList = ({
  privacyNotices,
}: {
  privacyNotices: PrivacyNoticeResponse[];
}) => {
  if (privacyNotices.length === 0) {
    return null;
  }

  return (
    <div className="max-h-60 overflow-y-auto">
      <ul className="m-0 list-inside list-disc pl-2">
        {privacyNotices.map((notice) => (
          <li key={notice.id} className="list-none">
            <ul className="m-0 list-inside list-disc">
              <li className="py-1">{notice.name}</li>
              {notice.children &&
                notice.children.length > 0 &&
                notice.children.map((child) => (
                  <li key={child.id} className="py-1 pl-5">
                    {child.name}
                  </li>
                ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
};

const ExperienceConfigSection = ({
  region,
  onRegionChange,
  propertyId,
  onPropertyIdChange,
  onFetchExperience,
  isLoading,
  errorMessage,
  privacyNotices,
}: ExperienceConfigSectionProps) => {
  return (
    <Flex vertical gap="small">
      <Typography.Title level={3}>Configuration</Typography.Title>

      <Flex gap="large">
        {/* Left Column - Configuration */}
        <Flex vertical flex={1} style={{ minWidth: 0 }}>
          <Typography.Text strong className="mb-2 block">
            Experience region
          </Typography.Text>
          <Flex gap="small" className="mb-4">
            <Input
              placeholder="Enter region (e.g., us_ca)"
              value={region}
              onChange={(e) => onRegionChange(e.target.value)}
              className="w-64"
            />
            <Button
              type="primary"
              onClick={onFetchExperience}
              loading={isLoading}
              disabled={!region}
            >
              Fetch experience
            </Button>
          </Flex>

          <Typography.Text strong className="mb-2 block">
            Property ID (optional)
          </Typography.Text>
          <Typography.Text type="secondary" className="mb-2 block">
            Leave empty to retrieve experience with no property
          </Typography.Text>
          <Flex gap="small" className="mb-4">
            <Input
              placeholder="Property ID (e.g FDS-1234)"
              value={propertyId}
              onChange={(e) => onPropertyIdChange(e.target.value)}
              className="w-64"
            />
          </Flex>

          {errorMessage && (
            <Typography.Text type="danger" className="mb-4 block">
              {errorMessage}
            </Typography.Text>
          )}
        </Flex>

        {/* Right Column - Available Notices */}
        <Flex vertical flex={1}>
          <PreviewCard
            title="Available notices"
            height="200px"
            headerColor={palette.FIDESUI_MINOS}
            emptyMessage="Available notices will appear here after fetching experience"
          >
            {privacyNotices.length > 0 ? (
              <PrivacyNoticesList privacyNotices={privacyNotices} />
            ) : null}
          </PreviewCard>
        </Flex>
      </Flex>
    </Flex>
  );
};

export default ExperienceConfigSection;
