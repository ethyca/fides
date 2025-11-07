import type { Key } from "antd/es/table/interface";
import { AntButton as Button, AntTypography as Typography } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

import type { ConsentPreferenceCreate } from "~/types/api/models/ConsentPreferenceCreate";
import type { ConsentResponse } from "~/types/api/models/ConsentResponse";
import { UserConsentPreference } from "~/types/api/models/UserConsentPreference";
import { useSavePrivacyPreferencesMutation } from "~/features/common/v3-api.slice";
import CascadeConsentToggle from "./CascadeConsentToggle";
import PreviewCard from "./PreviewCard";
import RealDataTree from "./RealDataTree";

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
  cascadeConsent: boolean;
  onCascadeConsentChange: (enabled: boolean) => void;
  privacyNotices: PrivacyNoticeResponse[];
  preferenceState: PreferenceState;
  noticeMappings: NoticeMappings;
  experienceConfigHistoryId: string | null;
  email: string;
  hasCurrentResponse: boolean;
}

const SavePreferencesSection = ({
  cascadeConsent,
  onCascadeConsentChange,
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

    // Apply cascade filtering if enabled
    let keysToProcess = changedKeys;
    if (cascadeConsent) {
      keysToProcess = changedKeys.filter((noticeKey) => {
        // Check if this key is a child
        const parentKey = childToParentMap.get(noticeKey);
        if (parentKey) {
          // This is a child. Only include it if its parent is NOT in the changed keys
          return !changedKeys.includes(parentKey);
        }
        // This is not a child (it's a parent or standalone), always include it
        return true;
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
        override_children: cascadeConsent,
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
    cascadeConsent,
    childToParentMap,
    experienceConfigHistoryId,
    email,
    savePreferences,
    onFetchedKeysChange,
    checkedKeys,
  ]);
  return (
    <div className="flex gap-6">
      {/* Left Column - Tree and Save */}
      <div className="min-w-0 flex-1">
        <Typography.Text strong className="mb-2 block text-sm">
          Current preferences
        </Typography.Text>

        {hasCurrentResponse ? (
          <>
            <Typography.Text strong className="mb-2 block text-sm">
              Consent behavior
            </Typography.Text>
            <div className="mb-4">
              <CascadeConsentToggle
                isEnabled={cascadeConsent}
                onToggle={onCascadeConsentChange}
              />
            </div>

            <RealDataTree
              privacyNotices={privacyNotices}
              checkedKeys={checkedKeys}
              onCheckedKeysChange={onCheckedKeysChange}
              cascadeConsent={cascadeConsent}
            />

            <Button
              type="primary"
              onClick={handleSavePreferences}
              loading={isSaving}
              disabled={!hasChanges}
              className="mt-4"
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
          <div className="rounded border border-dashed border-gray-300 bg-gray-50 p-4 text-center">
            <Typography.Text type="secondary">
              Fetch current preferences to manage user consent
            </Typography.Text>
          </div>
        )}
      </div>

      {/* Right Column - POST Response Preview */}
      <div className="min-w-0 flex-1">
        <PreviewCard title="POST response">
          {postResponse ? (
            <>
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
            </>
          ) : (
            <div className="flex h-full items-center justify-center">
              <Typography.Text type="secondary">
                POST response will appear here after saving preferences
              </Typography.Text>
            </div>
          )}
        </PreviewCard>
      </div>
    </div>
  );
};

export default SavePreferencesSection;
