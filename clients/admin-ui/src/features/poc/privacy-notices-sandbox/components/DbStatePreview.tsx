import { AntTypography as Typography } from "fidesui";

import PreviewCard from "./PreviewCard";

const DbStatePreview = ({
  dbState,
}: {
  dbState: Record<string, "opt_in" | "opt_out">;
}) => {
  return (
    <PreviewCard title="Current DB State">
      <Typography.Text strong className="mb-2 block text-sm text-purple-600">
        Raw DB State
      </Typography.Text>
      <pre className="m-0 whitespace-pre-wrap">
        {JSON.stringify(dbState, null, 2)}
      </pre>
    </PreviewCard>
  );
};

export default DbStatePreview;
