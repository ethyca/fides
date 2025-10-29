import { formatDistance } from "date-fns";
import { AntText as Text, AntTooltip as Tooltip } from "fidesui";
import React from "react";

import { formatDate, sentenceCase } from "../../../../common/utils";
import { LabeledText } from "./labels";

export const ReceivedOn = ({ createdAt }: { createdAt: string }) => (
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
