import { Text } from "fidesui";

import PreviewCard from "./PreviewCard";

const DbStatePreview = ({
  dbState,
}: {
  dbState: Record<string, "opt_in" | "opt_out">;
}) => {
  return (
    <PreviewCard title="Current DB State">
      <Text fontSize="sm" fontWeight="bold" mb={2} color="purple.600">
        Raw DB State
      </Text>
      <pre className="m-0 whitespace-pre-wrap">
        {JSON.stringify(dbState, null, 2)}
      </pre>
    </PreviewCard>
  );
};

export default DbStatePreview;
