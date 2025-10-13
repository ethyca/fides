import { AntButton as Button, AntTooltip as Tooltip, Icons } from "fidesui";
import Link from "next/link";
import React from "react";

export const ViewButton = ({ id }: { id: string }) => (
  <Link
    key="view"
    legacyBehavior
    href={`/privacy-requests/${encodeURIComponent(id)}`}
  >
    <Tooltip title="View privacy request">
      <Button
        key="view"
        icon={<Icons.View />}
        aria-label="View Request"
        size="small"
        href={`/privacy-requests/${encodeURIComponent(id)}`}
      />
    </Tooltip>
  </Link>
);
