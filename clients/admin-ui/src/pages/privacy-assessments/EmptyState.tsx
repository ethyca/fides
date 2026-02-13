import { Button, Icons, Text, Typography } from "fidesui";

const { Title } = Typography;

interface EmptyStateProps {
  onGenerate: () => void;
  isGenerating: boolean;
}

export const EmptyState = ({ onGenerate, isGenerating }: EmptyStateProps) => (
  <div className="flex flex-col items-center justify-center px-10 py-20 text-center">
    <div className="mb-6 flex size-16 items-center justify-center rounded-lg bg-gray-100">
      <Icons.Document size={32} className="text-gray-400" />
    </div>
    <Title level={4} className="!mb-2">
      No privacy assessments yet
    </Title>
    <Text type="secondary" className="mb-6 block max-w-md text-sm">
      Generate privacy assessments to evaluate your systems against regulatory
      frameworks and identify compliance gaps.
    </Text>
    <Button
      type="primary"
      icon={<Icons.Add />}
      onClick={onGenerate}
      loading={isGenerating}
      disabled={isGenerating}
    >
      {isGenerating ? "Generating..." : "Generate privacy assessments"}
    </Button>
  </div>
);
