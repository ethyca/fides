import { AntButton as Button, AntLayout as Layout, Text } from "fidesui";
import type { NextPage } from "next";
import { useCallback, useMemo, useState } from "react";

import PageHeader from "~/features/common/PageHeader";

import {
  ConsentMechanismToggle,
  DbStatePreview,
  DisableChildrenTree,
  GetApiPreview,
  PostApiPreview,
} from "./components";
import {
  ALL_KEYS,
  PARENT_KEY,
  PARENT_KEY_WITH_UUID,
  TREE_NODES,
} from "./constants";
import type { CheckedKeysType, ConsentMechanism } from "./types";

const { Content } = Layout;

const PrivacyNoticesSandbox: NextPage = () => {
  const [consentMechanism, setConsentMechanism] =
    useState<ConsentMechanism>("opt-out");
  const [checkedKeys, setCheckedKeys] = useState<CheckedKeysType>(ALL_KEYS);
  const [savedCheckedKeys, setSavedCheckedKeys] =
    useState<CheckedKeysType>(ALL_KEYS);
  const [previousSavedKeys, setPreviousSavedKeys] =
    useState<CheckedKeysType>(ALL_KEYS);
  const [dbState, setDbState] = useState<Record<string, "opt_in" | "opt_out">>(
    {},
  );

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

  const handleSave = useCallback(() => {
    setPreviousSavedKeys(savedCheckedKeys); // Store the previous saved state
    setSavedCheckedKeys(checkedKeys); // Update saved state to current

    // Update DB state with changes
    const currentArray = Array.isArray(checkedKeys)
      ? checkedKeys
      : checkedKeys.checked || [];
    const previousArray = Array.isArray(savedCheckedKeys)
      ? savedCheckedKeys
      : savedCheckedKeys.checked || [];

    const changedKeys = ALL_KEYS.filter((key) => {
      const isCurrentlyChecked = currentArray.includes(key);
      const wasPreviouslyChecked = previousArray.includes(key);
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
        const isChecked = currentArray.includes(key);
        newState[noticeKey] = isChecked ? "opt_in" : "opt_out";
      });
      return newState;
    });
  }, [checkedKeys, savedCheckedKeys]);

  return (
    <Layout>
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Privacy Notices Sandbox" />

        <div style={{ marginTop: "20px", display: "flex", gap: "24px" }}>
          {/* Left Column - Consent Management */}
          <div style={{ flex: "1", minWidth: "0" }}>
            <Text fontSize="md" fontWeight="bold" mb={4}>
              Notice configuration
            </Text>
            <ConsentMechanismToggle
              mechanism={consentMechanism}
              onMechanismChange={handleMechanismChange}
            />

            <Text fontSize="md" fontWeight="bold" mb={4}>
              Manage your consent preferences
            </Text>
            <DisableChildrenTree
              checkedKeys={checkedKeys}
              onCheckedKeysChange={setCheckedKeys}
            />

            <Button
              type="primary"
              onClick={handleSave}
              style={{ marginTop: "16px" }}
            >
              Save Preferences
            </Button>
          </div>

          {/* Right Column - POST API Preview */}
          <div style={{ flex: "1", minWidth: "0" }}>
            <PostApiPreview
              currentSavedKeys={savedCheckedKeys}
              previousSavedKeys={previousSavedKeys}
              mechanismDefaults={mechanismDefaults}
            />
          </div>
        </div>

        {/* GET API Preview Section */}
        <div style={{ marginTop: "24px" }}>
          <GetApiPreview
            dbState={dbState}
            consentMechanism={consentMechanism}
          />
        </div>

        {/* DB State Preview Section */}
        <div style={{ marginTop: "24px" }}>
          <DbStatePreview dbState={dbState} />
        </div>
      </Content>
    </Layout>
  );
};

export default PrivacyNoticesSandbox;
