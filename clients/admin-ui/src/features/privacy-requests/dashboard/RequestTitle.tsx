import { AntText as Text, AntTooltip as Tooltip, Icons } from "fidesui";
import React from "react";

export const RequestTitle = ({
  id,
  policyName,
}: {
  id: string;
  policyName: string;
}) => (
  <Text
    copyable={{
      text: id,
      icon: (
        <Tooltip title="Copy request ID">
          <Icons.Copy style={{ marginTop: "4px" }} />
        </Tooltip>
      ),
      tooltips: null,
    }}
    style={{
      display: "flex",
      gap: "8px",
      minWidth: "100px",
    }}
  >
    {policyName}
  </Text>
);
