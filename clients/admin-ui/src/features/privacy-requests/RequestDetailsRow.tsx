import { AntTypography as Typography } from "fidesui";

interface RequestDetailsRowProps {
  label: string;
  children: React.ReactNode;
}

const RequestDetailsRow = ({ label, children }: RequestDetailsRowProps) => (
  <div className="flex items-center">
    <div className="flex-1 pr-2">
      <Typography.Text>{label}:</Typography.Text>
    </div>
    <div className="flex-1">{children}</div>
  </div>
);

export default RequestDetailsRow;
