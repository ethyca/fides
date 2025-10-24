import type { Key } from "antd/es/table/interface";
import {
  AntButton as Button,
  AntLayout as Layout,
  AntTree as Tree,
  Switch,
  Text,
} from "fidesui";
import type { NextPage } from "next";
import { useCallback, useMemo, useState } from "react";

import PageHeader from "~/features/common/PageHeader";

const { Content } = Layout;

// Constants
const PARENT_KEY = "email_marketing" as const;

// Hardcoded UUIDs for each tree node
const PARENT_KEY_WITH_UUID = `${PARENT_KEY}-a1b2c3d4-e5f6-7890-abcd-ef1234567890`;

const TREE_NODES = [
  {
    title: "reward_points",
    key: "reward_points-b2c3d4e5-f6g7-8901-bcde-f23456789012",
  },
  {
    title: "current_account_benefits",
    key: "current_account_benefits-c3d4e5f6-g7h8-9012-cdef-345678901234",
  },
  {
    title: "credit_card_offers",
    key: "credit_card_offers-d4e5f6g7-h8i9-0123-defg-456789012345",
  },
  {
    title: "checking_and_saving_offers",
    key: "checking_and_saving_offers-e5f6g7h8-i9j0-1234-efgh-567890123456",
  },
  {
    title: "credit_monitoring",
    key: "credit_monitoring-f6g7h8i9-j0k1-2345-fghi-678901234567",
  },
  {
    title: "auto_financing",
    key: "auto_financing-g7h8i9j0-k1l2-3456-ghij-789012345678",
  },
];

const ALL_KEYS: Key[] = [
  PARENT_KEY_WITH_UUID,
  ...TREE_NODES.map((node) => node.key),
];
const INITIAL_EXPANDED_KEYS: Key[] = [PARENT_KEY_WITH_UUID];

// Types
type CheckedKeysType = Key[] | { checked: Key[]; halfChecked: Key[] };
type ConsentMechanism = "opt-in" | "opt-out";

interface TreeDataNode {
  title: string;
  key: string;
  disabled?: boolean;
  children?: TreeDataNode[];
}

// POST API Preview Component
const PostApiPreview = ({
  currentSavedKeys,
  previousSavedKeys,
}: {
  currentSavedKeys: CheckedKeysType;
  previousSavedKeys: CheckedKeysType;
}) => {
  const generateMockRequest = useCallback(() => {
    const currentArray = Array.isArray(currentSavedKeys)
      ? currentSavedKeys
      : currentSavedKeys.checked || [];

    const previousArray = Array.isArray(previousSavedKeys)
      ? previousSavedKeys
      : previousSavedKeys.checked || [];

    // Find notices that have changed between saves
    const changedKeys = ALL_KEYS.filter((key) => {
      const isInCurrentSave = currentArray.includes(key);
      const wasInPreviousSave = previousArray.includes(key);
      return isInCurrentSave !== wasInPreviousSave;
    });

    // If no notices have changed, don't show a request
    if (changedKeys.length === 0) {
      return null;
    }

    // Generate preferences array only for changed items
    const preferences = changedKeys.map((key) => {
      const isChecked = currentArray.includes(key);
      const value = isChecked ? "opt_in" : "opt_out";

      // Find the title from the tree structure
      let noticeKey;
      if (key === PARENT_KEY_WITH_UUID) {
        noticeKey = PARENT_KEY;
      } else {
        const treeNode = TREE_NODES.find((node) => node.key === key);
        noticeKey = treeNode ? treeNode.title : key.toString();
      }

      const noticeHistoryId = key.toString(); // Use the tree key as the history ID

      return {
        notice_key: noticeKey,
        value,
        notice_history_id: noticeHistoryId,
        meta: { timestamp: new Date().toISOString() },
      };
    });

    return {
      preferences,
    };
  }, [currentSavedKeys, previousSavedKeys]);

  const mockRequest = generateMockRequest();

  return (
    <div>
      <Text fontSize="md" fontWeight="bold" mb={4}>
        API Calls Preview
      </Text>
      <div
        style={{
          backgroundColor: "#f8f9fa",
          border: "1px solid #e9ecef",
          borderRadius: "8px",
          padding: "16px",
          height: "400px",
          fontFamily: "monospace",
          fontSize: "12px",
          overflow: "auto",
        }}
      >
        {mockRequest ? (
          <>
            <Text fontSize="sm" fontWeight="bold" mb={2} color="blue.600">
              POST /api/v3/privacy-preferences
            </Text>
            <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
              {JSON.stringify(mockRequest, null, 2)}
            </pre>
          </>
        ) : (
          <Text fontSize="sm" color="gray.500" fontStyle="italic">
            No API request will be made until preferences are selected.
          </Text>
        )}
      </div>
    </div>
  );
};

// GET API Preview Component
const GetApiPreview = ({
  dbState,
  consentMechanism,
}: {
  dbState: Record<string, "opt_in" | "opt_out">;
  consentMechanism: ConsentMechanism;
}) => {
  const generateGetResponse = useCallback(() => {
    const parentValue = dbState[PARENT_KEY];

    // If no parent value in DB, use mechanism default
    // opt-in mechanism = default is opt_out (must actively opt in)
    // opt-out mechanism = default is opt_in (must actively opt out)
    let effectiveParentValue: "opt_in" | "opt_out";
    if (parentValue !== undefined) {
      effectiveParentValue = parentValue;
    } else {
      effectiveParentValue =
        consentMechanism === "opt-in" ? "opt_out" : "opt_in";
    }

    const preferences: any[] = [];

    // Add parent preference
    preferences.push({
      notice_key: PARENT_KEY,
      preference: effectiveParentValue,
      notice_history_id: PARENT_KEY_WITH_UUID,
      parent_key: null,
    });

    // Add child preferences with consolidation logic
    TREE_NODES.forEach((node) => {
      let childValue: "opt_in" | "opt_out";

      if (effectiveParentValue === "opt_out") {
        // Rule 1: Parent opt_out overrides all children
        childValue = "opt_out";
      } else {
        // Parent is opt_in
        const explicitChildValue = dbState[node.title];
        if (explicitChildValue) {
          // Rule 3: Use explicit child value
          childValue = explicitChildValue;
        } else {
          // Rule 2: Inherit parent value (or use mechanism default if no parent in DB)
          childValue = effectiveParentValue;
        }
      }

      preferences.push({
        notice_key: node.title,
        preference: childValue,
        notice_history_id: node.key,
        parent_key: PARENT_KEY,
      });
    });

    return { preferences };
  }, [dbState, consentMechanism]);

  const getResponse = generateGetResponse();

  return (
    <div>
      <Text fontSize="md" fontWeight="bold" mb={4}>
        Current Preferences (consolidated)
      </Text>
      <div
        style={{
          backgroundColor: "#f8f9fa",
          border: "1px solid #e9ecef",
          borderRadius: "8px",
          padding: "16px",
          height: "400px",
          fontFamily: "monospace",
          fontSize: "12px",
          overflow: "auto",
        }}
      >
        <Text fontSize="sm" fontWeight="bold" mb={2} color="green.600">
          GET /api/v3/privacy-preferences/current?notice_key=email_marketing
        </Text>
        <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
          {JSON.stringify(getResponse, null, 2)}
        </pre>
      </div>
    </div>
  );
};

// DB State Preview Component
const DbStatePreview = ({
  dbState,
}: {
  dbState: Record<string, "opt_in" | "opt_out">;
}) => {
  return (
    <div>
      <Text fontSize="md" fontWeight="bold" mb={4}>
        Current DB State
      </Text>
      <div
        style={{
          backgroundColor: "#f8f9fa",
          border: "1px solid #e9ecef",
          borderRadius: "8px",
          padding: "16px",
          height: "300px",
          fontFamily: "monospace",
          fontSize: "12px",
          overflow: "auto",
        }}
      >
        <Text fontSize="sm" fontWeight="bold" mb={2} color="purple.600">
          Raw DB State
        </Text>
        <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
          {JSON.stringify(dbState, null, 2)}
        </pre>
      </div>
    </div>
  );
};

// Consent Mechanism Toggle Component
const ConsentMechanismToggle = ({
  mechanism,
  onMechanismChange,
}: {
  mechanism: ConsentMechanism;
  onMechanismChange: (mechanism: ConsentMechanism) => void;
}) => {
  const handleToggle = useCallback(
    (checked: boolean) => {
      const newMechanism: ConsentMechanism = checked ? "opt-out" : "opt-in";
      onMechanismChange(newMechanism);
    },
    [onMechanismChange],
  );

  return (
    <div
      style={{
        marginBottom: "16px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}
    >
      <Text fontSize="sm" fontWeight="medium">
        Consent Mechanism:
      </Text>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <Text
          fontSize="sm"
          color={mechanism === "opt-in" ? "primary.500" : "gray.500"}
        >
          Opt-in
        </Text>
        <Switch
          checked={mechanism === "opt-out"}
          onChange={(e) => handleToggle(e.target.checked)}
          size="sm"
        />
        <Text
          fontSize="sm"
          color={mechanism === "opt-out" ? "primary.500" : "gray.500"}
        >
          Opt-out
        </Text>
      </div>
      <Text fontSize="xs" color="gray.600">
        (
        {mechanism === "opt-out"
          ? "All checked by default"
          : "All unchecked by default"}
        )
      </Text>
    </div>
  );
};

const DisableChildrenTree = ({
  consentMechanism,
  onCheckedKeysChange,
}: {
  consentMechanism: ConsentMechanism;
  onCheckedKeysChange: (checkedKeys: CheckedKeysType) => void;
}) => {
  // State
  const [childrenDisabled, setChildrenDisabled] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<Key[]>(
    INITIAL_EXPANDED_KEYS,
  );
  const [checkedKeys, setCheckedKeys] = useState<CheckedKeysType>(
    consentMechanism === "opt-out" ? [...ALL_KEYS] : [],
  );
  const [selectedKeys, setSelectedKeys] = useState<Key[]>([]);
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  // Update checked keys when mechanism changes
  useMemo(() => {
    const newCheckedKeys = consentMechanism === "opt-out" ? [...ALL_KEYS] : [];
    setCheckedKeys(newCheckedKeys);
    // For opt-in, parent is unchecked so children should be disabled
    // For opt-out, parent is checked so children should be enabled
    setChildrenDisabled(consentMechanism === "opt-in");
  }, [consentMechanism]);

  // Helper functions
  const getCheckedArray = useCallback((keys: CheckedKeysType): Key[] => {
    return Array.isArray(keys) ? keys : keys.checked || [];
  }, []);

  const isParentChecked = useCallback(
    (keys: CheckedKeysType): boolean => {
      return getCheckedArray(keys).includes(PARENT_KEY_WITH_UUID);
    },
    [getCheckedArray],
  );

  // Event handlers
  const handleExpand = useCallback((expandedKeysValue: Key[]) => {
    // eslint-disable-next-line no-console
    console.log("onExpand", expandedKeysValue);
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  }, []);

  const handleCheck = useCallback(
    (checkedKeysValue: CheckedKeysType) => {
      // eslint-disable-next-line no-console
      console.log("onCheck", checkedKeysValue);
      // eslint-disable-next-line no-console
      console.log("checkedKeys", checkedKeys);

      const parentCheckedNow = isParentChecked(checkedKeysValue);
      const parentCheckedBefore = isParentChecked(checkedKeys);

      if (parentCheckedNow && !parentCheckedBefore) {
        // eslint-disable-next-line no-console
        console.log("parent changed to checked");
        setChildrenDisabled(false);
      } else if (!parentCheckedNow) {
        // eslint-disable-next-line no-console
        console.log("parent not checked");
        setChildrenDisabled(true);
      } else {
        setChildrenDisabled(false);
      }

      setCheckedKeys(checkedKeysValue);
      onCheckedKeysChange(checkedKeysValue);
    },
    [checkedKeys, isParentChecked, onCheckedKeysChange],
  );

  const handleSelect = useCallback((selectedKeysValue: Key[], info: any) => {
    // eslint-disable-next-line no-console
    console.log("onSelect", info);
    setSelectedKeys(selectedKeysValue);
  }, []);

  // Memoized tree data
  const treeData: TreeDataNode[] = useMemo(
    () => [
      {
        title: PARENT_KEY,
        key: PARENT_KEY_WITH_UUID,
        children: TREE_NODES.map((node) => ({
          title: node.title,
          key: node.key,
          disabled: childrenDisabled,
        })),
      },
    ],
    [childrenDisabled],
  );

  return (
    <Tree
      checkable
      checkStrictly
      onExpand={handleExpand}
      expandedKeys={expandedKeys}
      autoExpandParent={autoExpandParent}
      onCheck={handleCheck}
      checkedKeys={checkedKeys}
      onSelect={handleSelect}
      selectedKeys={selectedKeys}
      treeData={treeData}
    />
  );
};

const PrivacyNoticesSandbox: NextPage = () => {
  const [consentMechanism, setConsentMechanism] =
    useState<ConsentMechanism>("opt-in");
  const [checkedKeys, setCheckedKeys] = useState<CheckedKeysType>([]);
  const [savedCheckedKeys, setSavedCheckedKeys] = useState<CheckedKeysType>([]);
  const [previousSavedKeys, setPreviousSavedKeys] = useState<CheckedKeysType>(
    [],
  );
  const [dbState, setDbState] = useState<Record<string, "opt_in" | "opt_out">>(
    {},
  );

  const handleMechanismChange = useCallback((mechanism: ConsentMechanism) => {
    setConsentMechanism(mechanism);
    // Reset checked keys when mechanism changes
    const newCheckedKeys = mechanism === "opt-out" ? [...ALL_KEYS] : [];
    setCheckedKeys(newCheckedKeys);
    setSavedCheckedKeys(newCheckedKeys); // Set saved state to match the new default
    setPreviousSavedKeys(newCheckedKeys); // Reset previous saved state too

    // Clear DB state when mechanism changes (reset to empty)
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
              consentMechanism={consentMechanism}
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
