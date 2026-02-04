import { Text, Tooltip } from "fidesui";
import React from "react";

import { formatDate } from "../../../../common/utils";
import { LabeledText } from "./LabeledText";

export const ReceivedOn = ({
  createdAt,
}: {
  createdAt: string | undefined | null;
}) => {
  if (!createdAt) {
    return null;
  }

  return (
    <LabeledText label="Received">
      <Text type="secondary">
        <Tooltip title={formatDate(new Date(createdAt))}>
          {formatDate(new Date(createdAt), { showTime: false })}
        </Tooltip>
      </Text>
    </LabeledText>
  );
};
