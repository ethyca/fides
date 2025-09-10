import { AntTypography as Typography } from "fidesui";
import React from "react";

import { capitalize } from "~/features/common/utils";
import { ActionType } from "~/types/api";

import { Rule } from "../privacy-requests/types";

type RequestTypeProps = {
  rules: Rule[];
};

/**
 * Extracts and returns the unique action types from the rules.
 * @param rules Array of Rule objects.
 */
export const getActionTypes = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((d) => Object.values(ActionType).includes(d.action_type))
        .map((d) => d.action_type),
    ),
  );

const RequestType = ({ rules }: RequestTypeProps) => {
  const actionTypeLabels = getActionTypes(rules)
    .map((action) => capitalize(action))
    .map((action_type) => action_type);

  return <Typography.Text>{actionTypeLabels.join(" - ")}</Typography.Text>;
};

export default RequestType;
