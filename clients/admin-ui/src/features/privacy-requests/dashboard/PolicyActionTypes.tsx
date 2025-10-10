import { AntTag as Tag } from "fidesui";
import React from "react";

import { Rule } from "~/features/privacy-requests/types";
import { ActionType } from "~/types/api";

import { SubjectRequestActionTypeMap } from "../constants";

const getActionTypesFromRules = (rules: Rule[]): ActionType[] =>
  Array.from(
    new Set(
      rules
        .filter((rule) => Object.values(ActionType).includes(rule.action_type))
        .map((rule) => rule.action_type),
    ),
  );

export const PolicyActionTypes = ({ rules }: { rules: Rule[] }) => {
  return (
    <>
      {getActionTypesFromRules(rules)
        .map((actionType) => SubjectRequestActionTypeMap.get(actionType))
        .map((actionType) => (
          <Tag key={actionType}>{actionType}</Tag>
        ))}
    </>
  );
};
