import { Icons, Tag } from "fidesui";

import { DECISION_LABELS } from "./constants";
import { ActionType } from "./types";

interface DecisionTagProps {
  decision: ActionType;
}

const DecisionTag = ({ decision }: DecisionTagProps) => {
  const isAllow = decision === ActionType.ALLOW;
  return (
    <Tag
      color={isAllow ? "olive" : "default"}
      icon={
        isAllow ? <Icons.Checkmark size={12} /> : <Icons.WarningAlt size={12} />
      }
    >
      {DECISION_LABELS[decision] ?? decision}
    </Tag>
  );
};

export default DecisionTag;
