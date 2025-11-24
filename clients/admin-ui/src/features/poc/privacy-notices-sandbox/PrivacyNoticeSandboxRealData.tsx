import type { Key } from "antd/es/table/interface";
import {
  AntAlert as Alert,
  AntDivider as Divider,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  useLazyGetCurrentPreferencesQuery,
  useLazyGetPrivacyExperienceQuery,
} from "~/features/common/v3-api.slice";
import type { PrivacyNoticeResponse } from "~/types/api";
import type { ConsentPreferenceResponse } from "~/types/api/models/ConsentPreferenceResponse";
import type { PropagationPolicyKey } from "~/types/api/models/PropagationPolicyKey";
import { UserConsentPreference } from "~/types/api/models/UserConsentPreference";

import {
  ExperienceConfigSection,
  FetchPreferencesSection,
  SavePreferencesSection,
} from "./components";
import { EXPERIENCE_DEFAULTS } from "./constants";

const PrivacyNoticeSandboxRealData = () => {
  const [region, setRegion] = useState<string>(EXPERIENCE_DEFAULTS.REGION);
  const [propertyId, setPropertyId] = useState<string>("");
  const [email, setEmail] = useState("");
  const [policy, setPolicy] = useState<PropagationPolicyKey | null>(null);
  const [checkedKeys, setCheckedKeys] = useState<Key[]>([]);
  const [fetchedCheckedKeys, setFetchedCheckedKeys] = useState<Key[]>([]);
  const [explicitlyChangedKeys, setExplicitlyChangedKeys] = useState<Key[]>([]);
  const [selectedNoticeKeys, setSelectedNoticeKeys] = useState<string[]>([]);

  // Experience data
  const [privacyNotices, setPrivacyNotices] = useState<PrivacyNoticeResponse[]>(
    [],
  );
  const [experienceConfigHistoryId, setExperienceConfigHistoryId] = useState<
    string | null
  >(null);

  // API response state for preview
  const [getCurrentResponse, setGetCurrentResponse] = useState<
    ConsentPreferenceResponse[] | null
  >(null);

  // Error message state for experience fetching
  const [experienceErrorMessage, setExperienceErrorMessage] = useState("");

  const [fetchExperience, { isLoading: isLoadingExperience }] =
    useLazyGetPrivacyExperienceQuery();

  const [
    getCurrentPreferences,
    {
      isLoading: isLoadingCurrent,
      isError: isErrorCurrent,
      error: errorCurrent,
    },
  ] = useLazyGetCurrentPreferencesQuery();

  // Build maps and extract data from privacy notices in a single traversal
  const { noticeKeyToHistoryMap, parentNoticeKeys } = useMemo(() => {
    const historyMap = new Map<string, string>();
    const parentMap = new Map<string, string>();
    const parentKeys: Array<{ label: string; value: string }> = [];

    const traverse = (notices: PrivacyNoticeResponse[], parentKey?: string) => {
      notices.forEach((notice) => {
        const historyId =
          notice.translations?.[0]?.privacy_notice_history_id || notice.id;
        historyMap.set(notice.notice_key, historyId);

        if (parentKey) {
          parentMap.set(notice.notice_key, parentKey);
        } else {
          // Top-level notices are parents for the dropdown
          parentKeys.push({
            label: notice.name,
            value: notice.notice_key,
          });
        }

        if (notice.children?.length) {
          traverse(notice.children, notice.notice_key);
        }
      });
    };

    traverse(privacyNotices);
    return {
      noticeKeyToHistoryMap: historyMap,
      parentNoticeKeys: parentKeys,
    };
  }, [privacyNotices]);

  // Handle fetching privacy experience
  const handleFetchExperience = useCallback(async () => {
    setExperienceErrorMessage("");
    if (!region) {
      setExperienceErrorMessage("Please enter a region");
      return;
    }
    try {
      const result = await fetchExperience({
        region,
        show_disabled: EXPERIENCE_DEFAULTS.SHOW_DISABLED,
        ...(propertyId && { property_id: propertyId }),
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

          // Reset checked keys, fetched keys, and selected notice keys
          setCheckedKeys([]);
          setFetchedCheckedKeys([]);
          setSelectedNoticeKeys([]);
        }
      }
    } catch (error) {
      setExperienceErrorMessage("Failed to fetch privacy experience");
    }
  }, [fetchExperience, region, propertyId]);

  // Handle fetching current preferences
  const handleFetchCurrentPreferences = useCallback(async () => {
    try {
      const params: { "identity.email": string; notice_keys?: string[] } = {
        "identity.email": email,
      };

      // Only add notice_keys if some are selected (not "All notices")
      if (selectedNoticeKeys.length > 0) {
        params.notice_keys = selectedNoticeKeys;
      }

      const response = await getCurrentPreferences(params).unwrap();

      setGetCurrentResponse(response);

      // Convert response to checked keys and populate the tree
      // Use notice_key from the response since that's what the tree uses as keys
      const optInKeys = response
        .filter((pref) => pref.value === UserConsentPreference.OPT_IN)
        .map((pref) => pref.notice_key);

      setCheckedKeys(optInKeys);
      setFetchedCheckedKeys(optInKeys);
      // Clear explicitly changed keys when fetching new preferences
      setExplicitlyChangedKeys([]);
    } catch (error) {
      // Error handling is done by RTK Query (isError, error props)
    }
  }, [email, selectedNoticeKeys, getCurrentPreferences]);

  return (
    <div className="mt-5 space-y-8">
      {/* Info Banner */}
      <Alert
        type="info"
        message="This page makes real API calls to the Consent V3 API."
        description={
          <>
            <Typography.Paragraph className="mb-0 mt-3">
              Before using this sandbox, ensure you have:
            </Typography.Paragraph>
            <ul className="mb-0 ml-6 mt-2 space-y-1">
              <li>
                The consent v3 API enabled via the env var{" "}
                <Typography.Text code>
                  FIDESPLUS__EXPERIMENTAL__CONSENT_V3_ENABLED=true
                </Typography.Text>
              </li>
              <li>An email identity definition configured in your system</li>
              <li>
                A privacy experience set up with at least one privacy notice in
                the selected region
              </li>
            </ul>
            <Typography.Paragraph className="mb-0 mt-3">
              If you don&apos;t want to make real API calls or set up a privacy
              experience, go to the &quot;Simulated data&quot; tab.
            </Typography.Paragraph>
          </>
        }
        showIcon
      />

      {/* Configuration Section */}
      <ExperienceConfigSection
        region={region}
        onRegionChange={setRegion}
        propertyId={propertyId}
        onPropertyIdChange={setPropertyId}
        onFetchExperience={handleFetchExperience}
        isLoading={isLoadingExperience}
        errorMessage={experienceErrorMessage}
        privacyNotices={privacyNotices}
      />

      <Divider />

      {/* User Preferences Section */}
      <Flex vertical gap="small">
        <Typography.Title level={3}>User preferences</Typography.Title>

        {privacyNotices.length === 0 && (
          <Empty description="Load an experience in order to manage user preferences" />
        )}

        {privacyNotices.length > 0 && (
          <div className="space-y-6">
            {/* Row 1: Fetch Preferences Section */}
            <FetchPreferencesSection
              email={email}
              onEmailChange={setEmail}
              selectedNoticeKeys={selectedNoticeKeys}
              onSelectedNoticeKeysChange={setSelectedNoticeKeys}
              parentNoticeKeys={parentNoticeKeys}
              onFetchCurrentPreferences={handleFetchCurrentPreferences}
              isLoading={isLoadingCurrent}
              isError={isErrorCurrent}
              error={errorCurrent ? getErrorMessage(errorCurrent) : null}
              getCurrentResponse={getCurrentResponse}
            />

            {/* Row 2: Save Preferences Section */}
            <SavePreferencesSection
              policy={policy}
              onPolicyChange={setPolicy}
              privacyNotices={privacyNotices}
              preferenceState={{
                checkedKeys,
                fetchedCheckedKeys,
                onCheckedKeysChange: setCheckedKeys,
                onFetchedKeysChange: setFetchedCheckedKeys,
              }}
              noticeMappings={{
                noticeKeyToHistoryMap,
              }}
              experienceConfigHistoryId={experienceConfigHistoryId}
              email={email}
              hasCurrentResponse={getCurrentResponse !== null}
              explicitlyChangedKeys={explicitlyChangedKeys}
              onExplicitlyChangedKeysChange={setExplicitlyChangedKeys}
            />
          </div>
        )}
      </Flex>
    </div>
  );
};

export default PrivacyNoticeSandboxRealData;
