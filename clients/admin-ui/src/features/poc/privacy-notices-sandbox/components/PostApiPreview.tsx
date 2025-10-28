import type { Key } from "antd/es/table/interface";
import { AntTypography as Typography } from "fidesui";
import { useCallback } from "react";

import {
  ALL_KEYS,
  PARENT_KEY,
  PARENT_KEY_WITH_UUID,
  TREE_NODES,
} from "../constants";
import type { CheckedKeysType } from "../types";
import PreviewCard from "./PreviewCard";

const PostApiPreview = ({
  currentSavedKeys,
  previousSavedKeys,
  mechanismDefaults,
}: {
  currentSavedKeys: CheckedKeysType;
  previousSavedKeys: CheckedKeysType;
  mechanismDefaults: Key[];
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
      const wasInBaseline =
        previousArray.length > 0
          ? previousArray.includes(key)
          : mechanismDefaults.includes(key);
      return isInCurrentSave !== wasInBaseline;
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
  }, [currentSavedKeys, previousSavedKeys, mechanismDefaults]);

  const mockRequest = generateMockRequest();

  return (
    <PreviewCard title="API Calls Preview">
      {mockRequest ? (
        <>
          <Typography.Text strong className="mb-2 block text-sm text-blue-600">
            POST /api/v3/privacy-preferences
          </Typography.Text>
          <pre className="m-0 whitespace-pre-wrap">
            {JSON.stringify(mockRequest, null, 2)}
          </pre>
        </>
      ) : (
        <Typography.Text type="secondary" italic className="text-sm">
          No API request made because preferences were not changed from last
          save.
        </Typography.Text>
      )}
    </PreviewCard>
  );
};

export default PostApiPreview;
