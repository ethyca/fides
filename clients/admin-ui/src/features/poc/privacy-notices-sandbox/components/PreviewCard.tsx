import { Text } from "fidesui";
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
      <Text fontSize="md" fontWeight="bold" mb={4}>
        {title}
      </Text>
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
