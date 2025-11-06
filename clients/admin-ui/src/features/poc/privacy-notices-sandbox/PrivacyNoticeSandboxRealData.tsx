import type { Key } from "antd/es/table/interface";
import { AntDivider as Divider, AntTypography as Typography } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

import {
  ExperienceConfigSection,
  FetchPreferencesSection,
  SavePreferencesSection,
} from "./components";
import { CONSENT_VALUES, EXPERIENCE_DEFAULTS } from "./constants";
import type { ConsentPreferenceResponse } from "./v3-api";
import {
  useLazyGetCurrentPreferencesQuery,
  useLazyGetPrivacyExperienceQuery,
} from "./v3-api";

const PrivacyNoticeSandboxRealData = () => {
  // Form state
  const [region, setRegion] = useState<string>(EXPERIENCE_DEFAULTS.REGION);
  const [email, setEmail] = useState("");
  const [cascadeConsent, setCascadeConsent] = useState(false);
  const [checkedKeys, setCheckedKeys] = useState<Key[]>([]);
  const [fetchedCheckedKeys, setFetchedCheckedKeys] = useState<Key[]>([]);
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

  // Error message state
  const [errorMessage, setErrorMessage] = useState("");

  // RTK Query hooks
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
  const { noticeKeyToHistoryMap, childToParentMap, parentNoticeKeys } =
    useMemo(() => {
      const historyMap = new Map<string, string>();
      const parentMap = new Map<string, string>();
      const parentKeys: Array<{ label: string; value: string }> = [];

      const traverse = (
        notices: PrivacyNoticeResponse[],
        parentKey?: string,
      ) => {
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
        childToParentMap: parentMap,
        parentNoticeKeys: parentKeys,
      };
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
        show_disabled: EXPERIENCE_DEFAULTS.SHOW_DISABLED,
        component: EXPERIENCE_DEFAULTS.COMPONENT,
        systems_applicable: EXPERIENCE_DEFAULTS.SYSTEMS_APPLICABLE,
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
      setErrorMessage("Failed to fetch privacy experience");
    }
  }, [fetchExperience, region]);

  // Helper to merge new preferences with existing checked keys
  // Preserves child states when parent is opted out
  const mergePreferencesWithExisting = useCallback(
    (
      newOptInKeys: string[],
      response: ConsentPreferenceResponse[],
    ): string[] => {
      // No existing preferences, just return new ones
      if (checkedKeys.length === 0) {
        return newOptInKeys;
      }

      // Find parents that are opted out
      const optedOutParents = new Set(
        response
          .filter((pref) => pref.value === CONSENT_VALUES.OPT_OUT)
          .map((pref) => pref.notice_key),
      );

      // Start with new opt-in keys
      const updatedKeys = [...newOptInKeys];

      // Preserve child states when parent is opted out
      checkedKeys.forEach((key) => {
        const keyStr = key.toString();
        const parentKey = childToParentMap.get(keyStr);

        if (
          parentKey &&
          optedOutParents.has(parentKey) &&
          !updatedKeys.includes(keyStr)
        ) {
          updatedKeys.push(keyStr);
        }
      });

      return updatedKeys;
    },
    [checkedKeys, childToParentMap],
  );

  // Handle fetching current preferences
  const handleFetchCurrentPreferences = useCallback(async () => {
    setErrorMessage("");

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
        .filter((pref) => pref.value === CONSENT_VALUES.OPT_IN)
        .map((pref) => pref.notice_key);

      // Merge with existing preferences (preserves child states when parent is opted out)
      const finalKeys = mergePreferencesWithExisting(optInKeys, response);
      setCheckedKeys(finalKeys);
      setFetchedCheckedKeys(finalKeys);
    } catch (error) {
      setErrorMessage("Failed to fetch current preferences");
    }
  }, [
    email,
    selectedNoticeKeys,
    getCurrentPreferences,
    mergePreferencesWithExisting,
  ]);

  return (
    <div className="mt-5 space-y-8">
      {/* Configuration Section */}
      <ExperienceConfigSection
        region={region}
        onRegionChange={setRegion}
        onFetchExperience={handleFetchExperience}
        isLoading={isLoadingExperience}
        errorMessage={errorMessage}
        privacyNotices={privacyNotices}
      />

      <Divider />

      {/* User Preferences Section */}
      <div>
        <Typography.Text strong className="mb-4 block text-base">
          User preferences
        </Typography.Text>

        {privacyNotices.length === 0 && (
          <div className="rounded border border-gray-200 bg-gray-50 p-4 text-center">
            <Typography.Text type="secondary">
              Load an experience in order to manage user preferences
            </Typography.Text>
          </div>
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
              error={errorCurrent}
              getCurrentResponse={getCurrentResponse}
            />

            {/* Row 2: Save Preferences Section */}
            <SavePreferencesSection
              cascadeConsent={cascadeConsent}
              onCascadeConsentChange={setCascadeConsent}
              privacyNotices={privacyNotices}
              preferenceState={{
                checkedKeys,
                fetchedCheckedKeys,
                onCheckedKeysChange: setCheckedKeys,
                onFetchedKeysChange: setFetchedCheckedKeys,
              }}
              noticeMappings={{
                noticeKeyToHistoryMap,
                childToParentMap,
              }}
              experienceConfigHistoryId={experienceConfigHistoryId}
              email={email}
              hasCurrentResponse={getCurrentResponse !== null}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivacyNoticeSandboxRealData;
