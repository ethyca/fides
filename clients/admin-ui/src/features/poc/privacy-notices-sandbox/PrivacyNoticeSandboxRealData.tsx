import type { Key } from "antd/es/table/interface";
import {
  AntButton as Button,
  AntDivider as Divider,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

import { CascadeConsentToggle, PreviewCard, RealDataTree } from "./components";
import type {
  ConsentPreferenceCreate,
  ConsentPreferenceResponse,
  ConsentResponse,
} from "./v3-api";
import {
  useLazyGetCurrentPreferencesQuery,
  useLazyGetPrivacyExperienceQuery,
  useSavePrivacyPreferencesMutation,
} from "./v3-api";

const PrivacyNoticeSandboxRealData = () => {
  // Form state
  const [region, setRegion] = useState<string>("us_ca");
  const [email, setEmail] = useState<string>("");
  const [getCurrentEmail, setGetCurrentEmail] = useState<string>("");
  const [cascadeConsent, setCascadeConsent] = useState<boolean>(false);
  const [checkedKeys, setCheckedKeys] = useState<Key[]>([]);
  const [selectedNoticeKeys, setSelectedNoticeKeys] = useState<string[]>([]);

  // Experience data
  const [privacyNotices, setPrivacyNotices] = useState<PrivacyNoticeResponse[]>(
    [],
  );
  const [experienceConfigHistoryId, setExperienceConfigHistoryId] = useState<
    string | null
  >(null);

  // API response states for preview
  const [postResponse, setPostResponse] = useState<ConsentResponse | null>(
    null,
  );
  const [getCurrentResponse, setGetCurrentResponse] = useState<
    ConsentPreferenceResponse[] | null
  >(null);

  // Error message state
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [emailError, setEmailError] = useState<string>("");
  const [getCurrentEmailError, setGetCurrentEmailError] = useState<string>("");

  // RTK Query hooks
  const [fetchExperience, { isLoading: isLoadingExperience }] =
    useLazyGetPrivacyExperienceQuery();

  const [
    savePreferences,
    {
      isLoading: isSavingPreferences,
      isError: isErrorSaving,
      error: errorSaving,
    },
  ] = useSavePrivacyPreferencesMutation();

  const [
    getCurrentPreferences,
    {
      isLoading: isLoadingCurrent,
      isError: isErrorCurrent,
      error: errorCurrent,
    },
  ] = useLazyGetCurrentPreferencesQuery();

  // Build a map of notice keys to history IDs for easy lookup
  const noticeKeyToHistoryMap = useMemo(() => {
    const map = new Map<string, string>();
    const traverse = (notices: PrivacyNoticeResponse[]) => {
      notices.forEach((notice) => {
        const historyId =
          notice.translations?.[0]?.privacy_notice_history_id || notice.id;
        map.set(historyId, notice.notice_key);
        if (notice.children) {
          traverse(notice.children);
        }
      });
    };
    traverse(privacyNotices);
    return map;
  }, [privacyNotices]);

  // Extract parent notice keys for the dropdown
  const parentNoticeKeys = useMemo(() => {
    const keys: Array<{ label: string; value: string }> = [];
    privacyNotices.forEach((notice) => {
      keys.push({
        label: notice.name,
        value: notice.notice_key,
      });
    });
    return keys;
  }, [privacyNotices]);

  // Build a map of child to parent history IDs
  const childToParentMap = useMemo(() => {
    const childToParent = new Map<string, string>();

    const traverse = (notices: PrivacyNoticeResponse[], parentId?: string) => {
      notices.forEach((notice) => {
        const historyId =
          notice.translations?.[0]?.privacy_notice_history_id || notice.id;

        // If this notice has a parent, map it
        if (parentId) {
          childToParent.set(historyId, parentId);
        }

        // If this notice has children, recursively traverse them
        if (notice.children && notice.children.length > 0) {
          traverse(notice.children, historyId);
        }
      });
    };

    traverse(privacyNotices);
    return childToParent;
  }, [privacyNotices]);

  // Handle fetching privacy experience
  const handleFetchExperience = useCallback(async () => {
    setErrorMessage("");
    if (!region) {
      setErrorMessage("Please enter a region");
      return;
    }
    try {
      const result = await fetchExperience({
        region,
        show_disabled: false,
        component: "overlay",
        systems_applicable: true,
      }).unwrap();

      // Get the first experience from the paginated response
      if (result.items && result.items.length > 0) {
        const experience = result.items[0];
        if (
          "privacy_notices" in experience &&
          experience.privacy_notices &&
          experience.privacy_notices.length > 0
        ) {
          setPrivacyNotices(experience.privacy_notices);

          // Get experience config history ID from the first translation
          const historyId =
            experience.experience_config?.translations?.[0]
              ?.privacy_experience_config_history_id || null;
          setExperienceConfigHistoryId(historyId);

          // Reset checked keys and selected notice keys
          setCheckedKeys([]);
          setSelectedNoticeKeys([]);
        }
      }
    } catch (error) {
      setErrorMessage("Failed to fetch privacy experience");
    }
  }, [fetchExperience, region]);

  // Handle saving preferences
  const handleSavePreferences = useCallback(async () => {
    setErrorMessage("");
    setEmailError("");
    if (!email) {
      setEmailError("Please enter an email address");
      return;
    }

    if (checkedKeys.length === 0) {
      setErrorMessage("Please select at least one preference");
      return;
    }

    // Determine which keys to include in the request
    let keysToProcess = checkedKeys;

    // If cascade is enabled, filter out children when their parent is checked
    if (cascadeConsent) {
      const checkedSet = new Set(checkedKeys.map((k) => k.toString()));
      keysToProcess = checkedKeys.filter((key) => {
        const keyStr = key.toString();
        // Check if this key is a child
        const parentId = childToParentMap.get(keyStr);
        if (parentId) {
          // This is a child. Only include it if its parent is NOT checked
          return !checkedSet.has(parentId);
        }
        // This is not a child (it's a parent or standalone), always include it
        return true;
      });
    }

    // Build preferences array
    const preferences: ConsentPreferenceCreate[] = keysToProcess.map((key) => {
      const noticeKey = noticeKeyToHistoryMap.get(key as string) || "";
      return {
        notice_key: noticeKey,
        notice_history_id: key as string,
        value: "opt_in",
        experience_config_history_id: experienceConfigHistoryId,
        meta: {
          fides: {
            collected_at: new Date().toISOString(),
          },
        },
      };
    });

    try {
      const response = await savePreferences({
        body: {
          identity: {
            email: { value: email },
          },
          preferences,
        },
        override_children: cascadeConsent,
      }).unwrap();

      setPostResponse(response);
    } catch (error) {
      setErrorMessage("Failed to save preferences");
    }
  }, [
    email,
    checkedKeys,
    noticeKeyToHistoryMap,
    experienceConfigHistoryId,
    cascadeConsent,
    savePreferences,
    childToParentMap,
  ]);

  // Handle fetching current preferences
  const handleFetchCurrentPreferences = useCallback(async () => {
    setErrorMessage("");
    setGetCurrentEmailError("");
    if (!getCurrentEmail) {
      setGetCurrentEmailError("Please enter an email address");
      return;
    }

    try {
      const params: { "identity.email": string; notice_keys?: string[] } = {
        "identity.email": getCurrentEmail,
      };

      // Only add notice_keys if some are selected (not "All notices")
      if (selectedNoticeKeys.length > 0) {
        params.notice_keys = selectedNoticeKeys;
      }

      const response = await getCurrentPreferences(params).unwrap();

      setGetCurrentResponse(response);
    } catch (error) {
      setErrorMessage("Failed to fetch current preferences");
    }
  }, [getCurrentEmail, selectedNoticeKeys, getCurrentPreferences]);

  return (
    <div className="mt-5 space-y-8">
      {/* Configuration Section - Full Width */}
      <div>
        <Typography.Text strong className="mb-4 block text-base">
          Configuration
        </Typography.Text>

        <Typography.Text strong className="mb-2 block text-sm">
          Experience region
        </Typography.Text>
        <div className="mb-4 flex gap-2">
          <Input
            placeholder="Enter region (e.g., us_ca)"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="w-64"
          />
          <Button
            type="primary"
            onClick={handleFetchExperience}
            loading={isLoadingExperience}
            disabled={!region}
          >
            Fetch experience
          </Button>
        </div>

        <Typography.Text strong className="mb-2 block text-sm">
          Consent behavior
        </Typography.Text>
        <div className="mb-4">
          <CascadeConsentToggle
            isEnabled={cascadeConsent}
            onToggle={setCascadeConsent}
          />
        </div>

        {errorMessage && (
          <Typography.Text type="danger" className="mb-4 block">
            {errorMessage}
          </Typography.Text>
        )}
      </div>

      <Divider />

      {/* Preference Submission Section - Two Columns */}
      <div>
        <Typography.Text strong className="mb-4 block text-base">
          Preference submission
        </Typography.Text>

        {privacyNotices.length === 0 && (
          <div className="rounded border border-gray-200 bg-gray-50 p-4 text-center">
            <Typography.Text type="secondary">
              Load an experience in order to submit preferences
            </Typography.Text>
          </div>
        )}

        {privacyNotices.length > 0 && (
          <div className="flex gap-6">
            {/* Left Column - Form */}
            <div className="min-w-0 flex-1">
              <Typography.Text strong className="mb-2 block text-sm">
                User identity
              </Typography.Text>
              <Form.Item
                validateStatus={emailError ? "error" : undefined}
                help={emailError}
                className="mb-4"
              >
                <Input
                  placeholder="Enter email address"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) {
                      setEmailError("");
                    }
                  }}
                />
              </Form.Item>

              <Typography.Text strong className="mb-2 block text-sm">
                User preferences
              </Typography.Text>
              <RealDataTree
                privacyNotices={privacyNotices}
                checkedKeys={checkedKeys}
                onCheckedKeysChange={setCheckedKeys}
                cascadeConsent={cascadeConsent}
              />

              <Button
                type="primary"
                onClick={handleSavePreferences}
                loading={isSavingPreferences}
                disabled={checkedKeys.length === 0}
                className="mt-4"
              >
                Save preferences
              </Button>

              {isErrorSaving && (
                <Typography.Text type="danger" className="mt-2 block">
                  Error saving preferences:{" "}
                  {errorSaving && "message" in errorSaving
                    ? errorSaving.message
                    : "Unknown error"}
                </Typography.Text>
              )}
            </div>

            {/* Right Column - POST Response Preview */}
            <div className="min-w-0 flex-1">
              {postResponse ? (
                <PreviewCard title="POST Response">
                  <Typography.Text
                    strong
                    className="mb-2 block text-sm text-blue-600"
                  >
                    POST /api/v3/privacy-preferences
                    {cascadeConsent ? "?override_children=true" : ""}
                  </Typography.Text>
                  <pre className="m-0 whitespace-pre-wrap">
                    {JSON.stringify(postResponse, null, 2)}
                  </pre>
                </PreviewCard>
              ) : (
                <div className="rounded border border-gray-200 bg-gray-50 p-4 text-center">
                  <Typography.Text type="secondary">
                    POST response will appear here after saving preferences
                  </Typography.Text>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Divider />

      {/* Current Preferences Section - Two Columns */}
      <div>
        <Typography.Text strong className="mb-4 block text-base">
          Current preferences
        </Typography.Text>

        {privacyNotices.length === 0 && (
          <div className="rounded border border-gray-200 bg-gray-50 p-4 text-center">
            <Typography.Text type="secondary">
              Load an experience in order to be able to fetch current
              preferences
            </Typography.Text>
          </div>
        )}

        {privacyNotices.length > 0 && (
          <div className="flex gap-6">
            {/* Left Column - Form */}
            <div className="min-w-0 flex-1">
              <Typography.Text strong className="mb-2 block text-sm">
                User identity
              </Typography.Text>
              <Form.Item
                validateStatus={getCurrentEmailError ? "error" : undefined}
                help={getCurrentEmailError}
                className="mb-4"
              >
                <Input
                  placeholder="Enter email address"
                  value={getCurrentEmail}
                  onChange={(e) => {
                    setGetCurrentEmail(e.target.value);
                    if (getCurrentEmailError) {
                      setGetCurrentEmailError("");
                    }
                  }}
                />
              </Form.Item>

              <Typography.Text strong className="mb-2 block text-sm">
                Notice keys
              </Typography.Text>
              <Select
                mode="multiple"
                placeholder="All notices"
                value={selectedNoticeKeys}
                onChange={setSelectedNoticeKeys}
                options={parentNoticeKeys}
                className="mb-4 w-full"
                allowClear
                aria-label="Notice keys"
              />

              <Button
                type="primary"
                onClick={handleFetchCurrentPreferences}
                loading={isLoadingCurrent}
                disabled={!getCurrentEmail}
                className="mb-4"
              >
                Fetch current preferences
              </Button>

              {isErrorCurrent && (
                <Typography.Text type="danger" className="mt-2 block">
                  Error fetching current preferences:{" "}
                  {errorCurrent && "message" in errorCurrent
                    ? errorCurrent.message
                    : "Unknown error"}
                </Typography.Text>
              )}
            </div>

            {/* Right Column - GET Response Preview */}
            <div className="min-w-0 flex-1">
              {getCurrentResponse ? (
                <PreviewCard title="GET Current Preferences Response">
                  <Typography.Text
                    strong
                    className="mb-2 block text-sm text-green-600"
                  >
                    GET /api/v3/privacy-preferences/current?identity.email=
                    {getCurrentEmail}
                    {selectedNoticeKeys.length > 0 &&
                      `&notice_keys=${selectedNoticeKeys.join(",")}`}
                  </Typography.Text>
                  <pre className="m-0 whitespace-pre-wrap">
                    {JSON.stringify(getCurrentResponse, null, 2)}
                  </pre>
                </PreviewCard>
              ) : (
                <div className="rounded border border-gray-200 bg-gray-50 p-4 text-center">
                  <Typography.Text type="secondary">
                    GET response will appear here after fetching current
                    preferences
                  </Typography.Text>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivacyNoticeSandboxRealData;
