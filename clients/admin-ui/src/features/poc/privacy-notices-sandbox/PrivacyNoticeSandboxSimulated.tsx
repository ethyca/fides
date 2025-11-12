import type { Key } from "antd/es/table/interface";
import {
  AntButton as Button,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useMemo, useState } from "react";

import type { PrivacyNoticeResponse } from "~/types/api";

import {
  CascadeConsentToggle,
  ConsentMechanismRadioGroup,
  GetApiPreview,
  PostApiPreview,
  PreviewCard,
  PrivacyNoticesTree,
} from "./components";
import {
  ALL_KEYS,
  PARENT_KEY,
  PARENT_KEY_WITH_UUID,
  PRIVACY_NOTICES,
  TREE_NODES,
} from "./constants";
import type { ConsentMechanism } from "./types";

/**
 * Converts PRIVACY_NOTICES to use UUIDs as notice_key for PrivacyNoticesTree compatibility
 * PrivacyNoticesTree uses notice_key as the tree key, but we need UUIDs to match ALL_KEYS
 */
const convertNoticesForTree = (
  notices: PrivacyNoticeResponse[],
): PrivacyNoticeResponse[] => {
  return notices.map((notice) => ({
    ...notice,
    notice_key: notice.id, // Use id (UUID) as notice_key for tree key
    children: notice.children
      ? convertNoticesForTree(notice.children)
      : undefined,
  }));
};

const PrivacyNoticeSandboxSimulated = () => {
  const [consentMechanism, setConsentMechanism] =
    useState<ConsentMechanism>("opt-out");
  const [cascadeConsent, setCascadeConsent] = useState<boolean>(false);
  // Use Key[] internally for PrivacyNoticesTree compatibility
  const [checkedKeys, setCheckedKeys] = useState<Key[]>(ALL_KEYS);
  const [savedCheckedKeys, setSavedCheckedKeys] = useState<Key[]>(ALL_KEYS);
  const [previousSavedKeys, setPreviousSavedKeys] = useState<Key[]>(ALL_KEYS);
  const [dbState, setDbState] = useState<Record<string, "opt_in" | "opt_out">>(
    {},
  );

  // Convert PRIVACY_NOTICES for PrivacyNoticesTree (use UUIDs as notice_key)
  const treeNotices = useMemo(() => convertNoticesForTree(PRIVACY_NOTICES), []);

  // DERIVED STATE: The default checked keys for the current mechanism
  const mechanismDefaults = useMemo(
    () => (consentMechanism === "opt-out" ? ALL_KEYS : []),
    [consentMechanism],
  );

  const handleMechanismChange = useCallback((mechanism: ConsentMechanism) => {
    setConsentMechanism(mechanism);

    // Calculate new defaults for the mechanism
    const newDefaults = mechanism === "opt-out" ? ALL_KEYS : [];

    // Reset all states to match new mechanism
    setCheckedKeys(newDefaults);
    setSavedCheckedKeys(newDefaults);
    setPreviousSavedKeys(newDefaults);
    setDbState({});
  }, []);

  const handleCascadeToggle = useCallback(
    (enabled: boolean) => {
      setCascadeConsent(enabled);

      // Reset all states to match current mechanism defaults
      setCheckedKeys(mechanismDefaults);
      setSavedCheckedKeys(mechanismDefaults);
      setPreviousSavedKeys(mechanismDefaults);
      setDbState({});
    },
    [mechanismDefaults],
  );

  const handleSave = useCallback(() => {
    setPreviousSavedKeys(savedCheckedKeys); // Store the previous saved state
    setSavedCheckedKeys(checkedKeys); // Update saved state to current

    // Update DB state with changes
    const changedKeys = ALL_KEYS.filter((key) => {
      const isCurrentlyChecked = checkedKeys.includes(key);
      const wasPreviouslyChecked = savedCheckedKeys.includes(key);
      return isCurrentlyChecked !== wasPreviouslyChecked;
    });

    setDbState((prev) => {
      const newState = { ...prev };
      changedKeys.forEach((key) => {
        const noticeKey =
          key === PARENT_KEY_WITH_UUID
            ? PARENT_KEY
            : TREE_NODES.find((node) => node.key === key)?.title ||
              key.toString();
        const isChecked = checkedKeys.includes(key);
        newState[noticeKey] = isChecked ? "opt_in" : "opt_out";

        // If cascade is enabled and parent was changed, also update all children
        if (cascadeConsent && key === PARENT_KEY_WITH_UUID) {
          const value = isChecked ? "opt_in" : "opt_out";
          TREE_NODES.forEach((node) => {
            newState[node.title] = value;
          });
        }
      });
      return newState;
    });
  }, [checkedKeys, savedCheckedKeys, cascadeConsent]);

  return (
    <div className="mt-5">
      <Flex gap="large">
        {/* Left Column - Consent Management */}
        <Flex vertical flex={1}>
          <Typography.Text strong className="mb-4 block">
            Notice configuration
          </Typography.Text>
          <ConsentMechanismRadioGroup
            mechanism={consentMechanism}
            onMechanismChange={handleMechanismChange}
          />
          <Typography.Text strong className="mb-4 block">
            Consent behavior
          </Typography.Text>
          <CascadeConsentToggle
            isEnabled={cascadeConsent}
            onToggle={handleCascadeToggle}
          />

          <Typography.Text strong className="mb-4 block">
            User preferences
          </Typography.Text>
          <PrivacyNoticesTree
            privacyNotices={treeNotices}
            checkedKeys={checkedKeys}
            onCheckedKeysChange={setCheckedKeys}
            cascadeConsent={cascadeConsent}
          />

          <Button type="primary" onClick={handleSave} className="mt-4">
            Save preferences
          </Button>
        </Flex>

        {/* Right Column - POST API Preview */}
        <Flex vertical flex={1} style={{ minWidth: 0 }}>
          <PostApiPreview
            currentSavedKeys={savedCheckedKeys}
            previousSavedKeys={previousSavedKeys}
            cascadeConsent={cascadeConsent}
          />
        </Flex>
      </Flex>

      {/* GET API Preview Section */}
      <div className="mt-6">
        <GetApiPreview dbState={dbState} consentMechanism={consentMechanism} />
      </div>

      {/* DB State Preview Section */}
      <div className="mt-6">
        <PreviewCard
          title="Current DB State"
          header="Raw DB State"
          headerColor={palette.FIDESUI_TERRACOTTA}
          body={dbState}
        />
      </div>
    </div>
  );
};

export default PrivacyNoticeSandboxSimulated;
