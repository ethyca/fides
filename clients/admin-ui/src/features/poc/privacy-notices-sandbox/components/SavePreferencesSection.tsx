import type { Key } from "antd/es/table/interface";
import {
  AntButton as Button,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useMemo, useState } from "react";

import { useSavePrivacyPreferencesMutation } from "~/features/common/v3-api.slice";
import type { PrivacyNoticeResponse } from "~/types/api";
import type { ConsentPreferenceCreate } from "~/types/api/models/ConsentPreferenceCreate";
import type { ConsentResponse } from "~/types/api/models/ConsentResponse";
import type { OverrideMode } from "~/types/api/models/OverrideMode";
import { OverrideMode as OverrideModeEnum } from "~/types/api/models/OverrideMode";
import { UserConsentPreference } from "~/types/api/models/UserConsentPreference";

import OverrideModeDropdown from "./OverrideModeDropdown";
import PreviewCard from "./PreviewCard";
import PrivacyNoticesTree from "./PrivacyNoticesTree";

export interface PreferenceState {
  checkedKeys: Key[];
  fetchedCheckedKeys: Key[];
  onCheckedKeysChange: (keys: Key[]) => void;
  onFetchedKeysChange: (keys: Key[]) => void;
}

export interface NoticeMappings {
  noticeKeyToHistoryMap: Map<string, string>;
  childToParentMap: Map<string, string>;
}

interface SavePreferencesSectionProps {
  overrideMode: OverrideMode | null;
  onOverrideModeChange: (mode: OverrideMode | null) => void;
  privacyNotices: PrivacyNoticeResponse[];
  preferenceState: PreferenceState;
  noticeMappings: NoticeMappings;
  experienceConfigHistoryId: string | null;
  email: string;
  hasCurrentResponse: boolean;
  explicitlyChangedKeys: Key[];
  onExplicitlyChangedKeysChange: (keys: Key[]) => void;
}

const SavePreferencesSection = ({
  overrideMode,
  onOverrideModeChange,
  privacyNotices,
  preferenceState,
  noticeMappings,
  experienceConfigHistoryId,
  email,
  hasCurrentResponse,
  explicitlyChangedKeys,
  onExplicitlyChangedKeysChange,
}: SavePreferencesSectionProps) => {
  // Destructure grouped props for easier use
  const {
    checkedKeys,
    fetchedCheckedKeys,
    onCheckedKeysChange,
    onFetchedKeysChange,
  } = preferenceState;
  const { noticeKeyToHistoryMap, childToParentMap } = noticeMappings;
  // Local state for POST response
  const [postResponse, setPostResponse] = useState<ConsentResponse | null>(
    null,
  );

  // RTK Query mutation hook
  const [savePreferences, { isLoading: isSaving, isError, error }] =
    useSavePrivacyPreferencesMutation();

  // Helper to create key sets
  const createKeySets = useCallback(() => {
    return {
      fetchedSet: new Set(fetchedCheckedKeys.map((k) => k.toString())),
      currentSet: new Set(checkedKeys.map((k) => k.toString())),
    };
  }, [fetchedCheckedKeys, checkedKeys]);

  // Check if there are unsaved changes
  const hasChanges = useMemo(() => {
    const { fetchedSet, currentSet } = createKeySets();
    return Array.from(noticeKeyToHistoryMap.keys()).some(
      (noticeKey) => fetchedSet.has(noticeKey) !== currentSet.has(noticeKey),
    );
  }, [createKeySets, noticeKeyToHistoryMap]);

  // Handle saving preferences
  const handleSavePreferences = useCallback(async () => {
    // Calculate diff between current and fetched state
    const { fetchedSet, currentSet } = createKeySets();

    // Get all notice_keys
    const allNoticeKeys = Array.from(noticeKeyToHistoryMap.keys());

    // Find changed preferences
    const changedKeys = allNoticeKeys.filter((noticeKey) => {
      const wasChecked = fetchedSet.has(noticeKey);
      const isChecked = currentSet.has(noticeKey);
      return wasChecked !== isChecked;
    });

    // If no changes, don't make a request
    if (changedKeys.length === 0) {
      return;
    }

    // Use the explicitly changed keys (the ones the user actually clicked)
    // Filter to only include keys that are actually in the changed set
    const keysToSend = explicitlyChangedKeys.filter((key) =>
      changedKeys.includes(String(key)),
    );

    // Build preferences array with opt_in/opt_out based on current state
    const preferences: ConsentPreferenceCreate[] = keysToSend.map(
      (noticeKey) => {
        const noticeKeyStr = String(noticeKey);
        const historyId = noticeKeyToHistoryMap.get(noticeKeyStr) || "";
        const isChecked = currentSet.has(noticeKeyStr);
        return {
          notice_key: noticeKeyStr,
          notice_history_id: historyId,
          value: isChecked
            ? UserConsentPreference.OPT_IN
            : UserConsentPreference.OPT_OUT,
          experience_config_history_id: experienceConfigHistoryId,
          meta: {
            fides: {
              collected_at: new Date().toISOString(),
            },
          },
        };
      },
    );

    try {
      const response = await savePreferences({
        body: {
          identity: {
            email: { value: email },
          },
          preferences,
        },
        override_mode: overrideMode,
      }).unwrap();

      setPostResponse(response);
      // Update fetched state to current state after successful save
      onFetchedKeysChange(checkedKeys);
      // Clear explicitly changed keys after successful save
      onExplicitlyChangedKeysChange([]);
    } catch {
      // Error is handled by RTK Query state
    }
  }, [
    createKeySets,
    noticeKeyToHistoryMap,
    overrideMode,
    childToParentMap,
    experienceConfigHistoryId,
    email,
    savePreferences,
    onFetchedKeysChange,
    checkedKeys,
    explicitlyChangedKeys,
    onExplicitlyChangedKeysChange,
  ]);
  return (
    <Flex gap="large">
      {/* Left Column - Tree and Save */}
      <Flex vertical flex={1}>
        <Typography.Title level={4} style={{ fontSize: 14, marginBottom: 8 }}>
          Current preferences
        </Typography.Title>

        {hasCurrentResponse ? (
          <>
            <OverrideModeDropdown
              value={overrideMode}
              onChange={onOverrideModeChange}
            />

            <PrivacyNoticesTree
              privacyNotices={privacyNotices}
              checkedKeys={checkedKeys}
              onCheckedKeysChange={onCheckedKeysChange}
              cascadeConsent={
                overrideMode === OverrideModeEnum.DESCENDANTS ||
                overrideMode === OverrideModeEnum.ALL
              }
              cascadeAncestors={
                overrideMode === OverrideModeEnum.ANCESTORS ||
                overrideMode === OverrideModeEnum.ALL
              }
              onExplicitChange={(key) => {
                // Always track when user clicks a key
                // Remove the key if it's already there (user is toggling back)
                // then add it fresh to mark this as the latest action
                const filteredKeys = explicitlyChangedKeys.filter(
                  (k) => k !== key,
                );
                onExplicitlyChangedKeysChange([...filteredKeys, key]);
              }}
            />

            <Button
              type="primary"
              onClick={handleSavePreferences}
              loading={isSaving}
              disabled={!hasChanges}
              className="mt-4 self-start"
            >
              Save preferences
            </Button>

            {isError && (
              <Typography.Text type="danger" className="mt-2 block">
                Error saving preferences:{" "}
                {error && "message" in error ? error.message : "Unknown error"}
              </Typography.Text>
            )}
          </>
        ) : (
          <Flex vertical align="center" justify="center" flex={1}>
            <Empty description="Fetch current preferences to manage user consent" />
          </Flex>
        )}
      </Flex>

      {/* Right Column - POST Response Preview */}
      <Flex vertical flex={1} className="min-w-0">
        <PreviewCard
          title="POST response"
          header={
            postResponse
              ? `POST /api/v3/privacy-preferences${
                  overrideMode ? `?override_mode=${overrideMode}` : ""
                }`
              : null
          }
          headerColor={palette.FIDESUI_ALERT}
          body={postResponse}
          emptyMessage="POST response will appear here after saving preferences"
        />
      </Flex>
    </Flex>
  );
};

export default SavePreferencesSection;
