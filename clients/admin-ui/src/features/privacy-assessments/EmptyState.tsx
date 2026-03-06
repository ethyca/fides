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
    title="No assessments run yet"
    subTitle="Run assessments to evaluate your systems against regulatory frameworks and identify compliance gaps."
    extra={
      <Button type="primary" icon={<Icons.Add />} onClick={onRunAssessment}>
        Run assessment
      </Button>
    }
    className="mt-20"
  />
);
