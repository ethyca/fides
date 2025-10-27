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
        style={{
          backgroundColor: "#f8f9fa",
          border: "1px solid #e9ecef",
          borderRadius: "8px",
          padding: "16px",
          height,
          fontFamily: "monospace",
          fontSize: "12px",
          overflow: "auto",
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default PreviewCard;
