import {
  AntCard as Card,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";
import type { ReactNode } from "react";

interface PreviewCardProps {
  title: string;
  height?: string | number;
  header?: string | null;
  headerColor: string;
  body?: unknown;
  emptyMessage?: string;
  children?: ReactNode;
}

const PreviewCard = ({
  title,
  height = "400px",
  header,
  headerColor,
  body,
  emptyMessage,
  children,
}: PreviewCardProps) => {
  const renderContent = () => {
    // If children are provided, use them
    if (children) {
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
        <Flex
          vertical
          align="center"
          justify="center"
          className="h-full"
        >
          <Typography.Text type="secondary">{emptyMessage}</Typography.Text>
        </Flex>
      );
    }

    return null;
  };

  return (
    <div>
      <Typography.Text strong className="mb-4 block">
        {title}
      </Typography.Text>
      <Card
        className="bg-gray-50 font-mono text-xs"
        styles={{ body: { padding: "18px" } }}
      >
        <div className="overflow-auto" style={{ height }}>
          {header && (
            <Typography.Text
              strong
              size="sm"
              className="mb-2 block"
              style={{ color: headerColor }}
            >
              {header}
            </Typography.Text>
          )}
          {renderContent()}
        </div>
      </Card>
    </div>
  );
};

export default PreviewCard;
