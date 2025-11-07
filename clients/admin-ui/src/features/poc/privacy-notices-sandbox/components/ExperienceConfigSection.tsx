import {
  AntButton as Button,
  AntInput as Input,
  AntTypography as Typography,
} from "fidesui";

import type { PrivacyNoticeResponse } from "~/types/api";

import PreviewCard from "./PreviewCard";

interface ExperienceConfigSectionProps {
  region: string;
  onRegionChange: (region: string) => void;
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
                  <li
                    key={child.id}
                    className="py-1"
                    style={{ paddingLeft: "20px" }}
                  >
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
  onFetchExperience,
  isLoading,
  errorMessage,
  privacyNotices,
}: ExperienceConfigSectionProps) => {
  return (
    <div>
      <Typography.Text strong className="mb-4 block text-base">
        Configuration
      </Typography.Text>

      <div className="flex gap-6">
        {/* Left Column - Configuration */}
        <div className="min-w-0 flex-1">
          <Typography.Text strong className="mb-2 block text-sm">
            Experience region
          </Typography.Text>
          <div className="mb-4 flex gap-2">
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
          </div>

          {errorMessage && (
            <Typography.Text type="danger" className="mb-4 block">
              {errorMessage}
            </Typography.Text>
          )}
        </div>

        {/* Right Column - Available Notices */}
        <div className="min-w-0 flex-1">
          <PreviewCard
            title="Available notices"
            height="200px"
            emptyMessage="Available notices will appear here after fetching experience"
          >
            {privacyNotices.length > 0 && (
              <PrivacyNoticesList privacyNotices={privacyNotices} />
            )}
          </PreviewCard>
        </div>
      </div>
    </div>
  );
};

export default ExperienceConfigSection;
