import { AntTypography as Typography } from "fidesui";
import type { ReactNode } from "react";

interface PreviewCardProps {
  title: string;
  height?: string | number;
  header?: string | null;
  headerColor?: "green" | "blue" | "purple";
  body?: unknown;
  emptyMessage?: string;
  children?: ReactNode;
}

const PreviewCard = ({
  title,
  height = "400px",
  header,
  headerColor = "green",
  body,
  emptyMessage,
  children,
}: PreviewCardProps) => {
  const headerColorClass = {
    green: "text-green-600",
    blue: "text-blue-600",
    purple: "text-purple-600",
  }[headerColor];

  const renderContent = () => {
    // If children are provided, use them
    if (children !== undefined) {
      return children;
    }

    // If body is provided, render as JSON
    if (body !== undefined && body !== null) {
      return (
        <pre className="m-0 whitespace-pre-wrap">
          {JSON.stringify(body, null, 2)}
        </pre>
      );
    }

    // Otherwise, show empty message if provided
    if (emptyMessage) {
      return (
        <div className="flex h-full items-center justify-center">
          <Typography.Text type="secondary">{emptyMessage}</Typography.Text>
        </div>
      );
    }

    return null;
  };

  return (
    <div>
      <Typography.Text strong className="mb-4 block text-base">
        {title}
      </Typography.Text>
      <div
        className="overflow-auto rounded-lg border border-gray-200 bg-gray-50 p-4 font-mono text-xs"
        style={{ height }}
      >
        {header && (
          <Typography.Text
            strong
            className={`mb-2 block text-sm ${headerColorClass}`}
          >
            {header}
          </Typography.Text>
        )}
        {renderContent()}
      </div>
    </div>
  );
};

export default PreviewCard;
