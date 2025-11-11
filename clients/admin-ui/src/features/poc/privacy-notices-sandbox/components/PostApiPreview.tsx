import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback } from "react";

import {
  ALL_KEYS,
  PARENT_KEY,
  PARENT_KEY_WITH_UUID,
  TREE_NODES,
} from "../constants";
import type { CheckedKeysType, PreferenceItem } from "../types";
import PreviewCard from "./PreviewCard";

const PostApiPreview = ({
  currentSavedKeys,
  previousSavedKeys,
  cascadeConsent,
}: {
  currentSavedKeys: CheckedKeysType;
  previousSavedKeys: CheckedKeysType;
  cascadeConsent?: boolean;
}) => {
  const generateMockRequest = useCallback(() => {
    const currentArray = Array.isArray(currentSavedKeys)
      ? currentSavedKeys
      : currentSavedKeys.checked || [];

    const previousArray = Array.isArray(previousSavedKeys)
      ? previousSavedKeys
      : previousSavedKeys.checked || [];

    // Find notices that have changed from baseline
    const changedKeys = ALL_KEYS.filter((key) => {
      const isInCurrentSave = currentArray.includes(key);
      const wasInBaseline = previousArray.includes(key);
      return isInCurrentSave !== wasInBaseline;
    });

    // If cascade is enabled and parent is among the changed keys,
    // when setting parent opt_in, children are auto-checked so they show as "changed"
    // but we only want to show the parent in the API request
    const parentChanged = changedKeys.includes(PARENT_KEY_WITH_UUID);
    const keysToProcess =
      cascadeConsent && parentChanged ? [PARENT_KEY_WITH_UUID] : changedKeys;

    // If no notices have changed, don't show a request
    if (keysToProcess.length === 0) {
      return null;
    }

    // Generate preferences array only for changed items
    const preferences: PreferenceItem[] = keysToProcess.map((key) => {
      const isChecked = currentArray.includes(key);
      const value: "opt_in" | "opt_out" = isChecked ? "opt_in" : "opt_out";

      // Find the notice_key from TREE_NODES
      let noticeKey: string;
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
  }, [currentSavedKeys, previousSavedKeys, cascadeConsent]);

  const mockRequest = generateMockRequest();

  // Always show override_children query param when cascade is enabled
  const endpoint =
    cascadeConsent && mockRequest
      ? "POST /api/v3/privacy-preferences?override_children=true"
      : "POST /api/v3/privacy-preferences";

  return (
    <PreviewCard
      title="API Calls Preview"
      header={mockRequest ? endpoint : null}
      headerColor={palette.FIDESUI_ALERT}
      body={mockRequest}
      emptyMessage="No API request made because preferences were not changed from last save."
    />
  );
};

export default PostApiPreview;
