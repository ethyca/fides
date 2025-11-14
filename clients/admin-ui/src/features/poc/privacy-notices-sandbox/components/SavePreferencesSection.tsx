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

    // Apply filtering based on override mode
    let keysToProcess = changedKeys;

    if (overrideMode === OverrideModeEnum.DESCENDANTS) {
      // For DESCENDANTS: filter out children when their parent is also changed
      // Only send parent preferences, the API will cascade to descendants
      keysToProcess = changedKeys.filter((noticeKey) => {
        const parentKey = childToParentMap.get(noticeKey);
        if (parentKey) {
          // This is a child. Only include it if its parent is NOT in the changed keys
          return !changedKeys.includes(parentKey);
        }
        // This is not a child (it's a parent or standalone), always include it
        return true;
      });
    } else if (overrideMode === OverrideModeEnum.ANCESTORS) {
      // For ANCESTORS: filter out parents when their child is also changed
      // Only send child preferences, the API will cascade to ancestors
      keysToProcess = changedKeys.filter((noticeKey) => {
        // Check if any of this key's children are in the changed keys
        const hasChangedChild = changedKeys.some(
          (key) => childToParentMap.get(key) === noticeKey,
        );
        // Include this key only if none of its children are changed
        return !hasChangedChild;
      });
    } else if (overrideMode === OverrideModeEnum.ALL) {
      // For ALL: send all changed keys, API will handle both directions
      // Filter based on hierarchy to avoid redundancy
      keysToProcess = changedKeys.filter((noticeKey) => {
        const parentKey = childToParentMap.get(noticeKey);
        // Only include if parent is not also changed (prefer parent changes for efficiency)
        return !parentKey || !changedKeys.includes(parentKey);
      });
    }

    // Build preferences array with opt_in/opt_out based on current state
    const preferences: ConsentPreferenceCreate[] = keysToProcess.map(
      (noticeKey) => {
        const historyId = noticeKeyToHistoryMap.get(noticeKey) || "";
        const isChecked = currentSet.has(noticeKey);
        return {
          notice_key: noticeKey,
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
