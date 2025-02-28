import { AntTypography as Typography } from "fidesui";

import styles from "./RequestDetailsRow.module.scss";

interface RequestDetailsRowProps {
  label: string;
  children: React.ReactNode;
}

const RequestDetailsRow = ({ label, children }: RequestDetailsRowProps) => (
  <div className="flex items-center">
    <div className={`flex-1 pr-2 ${styles.label}`}>
      <Typography.Text>{label}:</Typography.Text>
    </div>
    <div className={`flex-1 ${styles.value}`}>{children}</div>
  </div>
);

export default RequestDetailsRow;
