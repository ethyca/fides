import { AntTypography as Typography } from "fidesui";
import type { ReactNode } from "react";

const PreviewCard = ({
  title,
  height = "400px",
  children,
}: {
  title: string;
  height?: string | number;
  children: ReactNode;
}) => {
  return (
    <div>
      <Typography.Text strong className="mb-4 block text-base">
        {title}
      </Typography.Text>
      <div
        className="overflow-auto rounded-lg border border-gray-200 bg-gray-50 p-4 font-mono text-xs"
        style={{ height }}
      >
        {children}
      </div>
    </div>
  );
};

export default PreviewCard;
