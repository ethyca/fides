import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

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
    <Flex gap={24}>
      {/* Left Column - Fetch Inputs */}
      <Flex vertical flex={1}>
        <Flex vertical className="pr-24">
          <Typography.Text strong className="mb-2 block">
            User email (identity)
          </Typography.Text>
          <Input
            placeholder="Enter email address"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            className="mb-4"
          />

          <Typography.Text strong className="mb-2 block">
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
            className="mb-4 self-start"
          >
            Fetch current preferences
          </Button>

          {isError && (
            <Typography.Text type="danger" className="mb-4 block">
              Error fetching current preferences:{" "}
              {error && "message" in error ? error.message : "Unknown error"}
            </Typography.Text>
          )}
        </Flex>
      </Flex>

      {/* Right Column - GET Response Preview */}
      <Flex vertical flex={1} style={{ minWidth: 0 }}>
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
          headerColor={palette.FIDESUI_SUCCESS}
          body={getCurrentResponse}
          emptyMessage="GET response will appear here after fetching preferences"
        />
      </Flex>
    </Flex>
  );
};

export default FetchPreferencesSection;
