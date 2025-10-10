import {
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { useRouter } from "next/router";
import React from "react";

export const RequestTitle = ({
  id,
  policyName,
}: {
  id: string;
  policyName: string;
}) => {
  const router = useRouter();

  return (
    <div className="flex min-w-[100px] gap-2">
      <Typography.Title level={3}>
        <Typography.Link
          href={`/privacy-requests/${id}`}
          variant="primary"
          onClick={(e) => {
            e.preventDefault();
            router.push(`/privacy-requests/${id}`);
          }}
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
      </Typography.Title>
    </div>
  );
};
