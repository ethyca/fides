import {
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import NextLink from "next/link";
import React from "react";

export const RequestTitle = ({
  id,
  policyName,
}: {
  id: string;
  policyName: string;
}) => (
  <div className="flex min-w-[100px] gap-2">
    <NextLink href={`/privacy-requests/${id}`}>
      <Typography.Link
        variant="primary"
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
      </Typography.Link>
    </NextLink>
  </div>
);
