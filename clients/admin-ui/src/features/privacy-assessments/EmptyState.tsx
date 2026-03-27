import { Avatar, Button, Icons, Result } from "fidesui";

interface EmptyStateProps {
  onRunAssessment: () => void;
}

export const EmptyState = ({ onRunAssessment }: EmptyStateProps) => (
  <Result
    icon={
      <Avatar
        shape="square"
        variant="outlined"
        size={64}
        icon={<Icons.Document size={32} />}
      />
    }
    title="Assess your privacy compliance"
    subTitle="Scan your systems, data maps, and policies to automatically generate assessments against regulatory frameworks."
    extra={
      <Button type="primary" icon={<Icons.Add />} onClick={onRunAssessment}>
        Scan &amp; generate assessments
      </Button>
    }
    className="mt-20"
  />
);
