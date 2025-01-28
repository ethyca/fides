import { Badge, Box } from "fidesui";
import { Rule } from "privacy-requests/types";
import React from "react";

import { capitalize } from "~/features/common/utils";
import { ActionType } from "~/types/api";

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
  const tags = getActionTypes(rules)
    .map((action) => capitalize(action))
    .map((action_type) => <Badge key={action_type}>{action_type}</Badge>);

  return <Box>{tags}</Box>;
};

export default RequestType;
