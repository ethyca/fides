import {
  AntButton as Button,
  AntInput as Input,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";

import type { ConsentPreferenceResponse } from "~/types/api/models/ConsentPreferenceResponse";

import PreviewCard from "./PreviewCard";

interface FetchPreferencesSectionProps {
  email: string;
  onEmailChange: (email: string) => void;
  selectedNoticeKeys: string[];
  onSelectedNoticeKeysChange: (keys: string[]) => void;
  parentNoticeKeys: Array<{ label: string; value: string }>;
  onFetchCurrentPreferences: () => void;
  isLoading: boolean;
  isError: boolean;
  error: any;
  getCurrentResponse: ConsentPreferenceResponse[] | null;
}

const FetchPreferencesSection = ({
  email,
  onEmailChange,
  selectedNoticeKeys,
  onSelectedNoticeKeysChange,
  parentNoticeKeys,
  onFetchCurrentPreferences,
  isLoading,
  isError,
  error,
  getCurrentResponse,
}: FetchPreferencesSectionProps) => {
  return (
    <div className="flex gap-6">
      {/* Left Column - Fetch Inputs */}
      <div className="min-w-0 flex-1">
        <Typography.Text strong className="mb-2 block text-sm">
          User email (identity)
        </Typography.Text>
        <Input
          placeholder="Enter email address"
          value={email}
          onChange={(e) => onEmailChange(e.target.value)}
          className="mb-4"
        />

        <Typography.Text strong className="mb-2 block text-sm">
          Notice keys
        </Typography.Text>
        <Select
          mode="multiple"
          placeholder="All notices"
          value={selectedNoticeKeys}
          onChange={onSelectedNoticeKeysChange}
          options={parentNoticeKeys}
          className="mb-4 w-full"
          allowClear
          aria-label="Notice keys"
        />

        <Button
          type="primary"
          onClick={onFetchCurrentPreferences}
          loading={isLoading}
          disabled={!email}
          className="mb-4"
        >
          Fetch current preferences
        </Button>

        {isError && (
          <Typography.Text type="danger" className="mb-4 block">
            Error fetching current preferences:{" "}
            {error && "message" in error ? error.message : "Unknown error"}
          </Typography.Text>
        )}
      </div>

      {/* Right Column - GET Response Preview */}
      <div className="min-w-0 flex-1">
        <PreviewCard
          title="GET response"
          header={
            getCurrentResponse
              ? `GET /api/v3/privacy-preferences/current?identity.email=${email}${
                  selectedNoticeKeys.length > 0
                    ? `&notice_keys=${selectedNoticeKeys.join(",")}`
                    : ""
                }`
              : null
          }
          headerColor="green"
          body={getCurrentResponse}
          emptyMessage="GET response will appear here after fetching preferences"
        />
      </div>
    </div>
  );
};

export default FetchPreferencesSection;
