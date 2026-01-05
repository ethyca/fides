import { formatDistance } from "date-fns";
import { Text, Tooltip } from "fidesui";
import React from "react";

import { formatDate, sentenceCase } from "../../../../common/utils";
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
          {sentenceCase(
            formatDistance(new Date(createdAt), new Date(), {
              addSuffix: true,
            }),
          )}
        </Tooltip>
      </Text>
    </LabeledText>
  );
};
