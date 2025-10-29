import { AntTypography as Typography } from "fidesui";
import { useCallback } from "react";

import { PARENT_KEY, PARENT_KEY_WITH_UUID, TREE_NODES } from "../constants";
import type { ConsentMechanism } from "../types";
import PreviewCard from "./PreviewCard";

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
    <PreviewCard title="Current Preferences (consolidated)">
      <Typography.Text strong className="mb-2 block text-sm text-green-600">
        GET /api/v3/privacy-preferences/current?notice_key=email_marketing
      </Typography.Text>
      <pre className="m-0 whitespace-pre-wrap">
        {JSON.stringify(getResponse, null, 2)}
      </pre>
    </PreviewCard>
  );
};

export default GetApiPreview;
