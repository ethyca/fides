import { formatDistance } from "date-fns";
import { AntText as Text } from "fidesui";
import React from "react";

import { sentenceCase } from "../../../../common/utils";
import { LabeledText } from "./labels";

export const ReceivedOn = ({ createdAt }: { createdAt: string }) => (
  <LabeledText label="Received">
    <Text type="secondary">
      {sentenceCase(
        formatDistance(new Date(createdAt), new Date(), {
          addSuffix: true,
        }),
      )}
    </Text>
  </LabeledText>
);
