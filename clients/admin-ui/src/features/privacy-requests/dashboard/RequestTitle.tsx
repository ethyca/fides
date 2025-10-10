import { AntText as Text, AntTooltip as Tooltip, Icons } from "fidesui";
import React from "react";

export const RequestTitle = ({
  id,
  policyName,
}: {
  id: string;
  policyName: string;
}) => (
  <div className="flex min-w-[100px] gap-2">
    <Text
      copyable={{
        text: id,
        icon: (
          <Tooltip title="Copy request ID">
            <div className="mt-1">
              <Icons.Copy />
            </div>
          </Tooltip>
        ),
        tooltips: null,
      }}
    >
      {policyName}
    </Text>
  </div>
);
