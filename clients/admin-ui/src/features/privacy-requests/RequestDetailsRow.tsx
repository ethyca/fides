import { AntTypography as Typography } from "fidesui";

import styles from "./RequestDetailsRow.module.scss";

interface RequestDetailsRowProps {
  label: string;
  children: React.ReactNode;
}

const RequestDetailsRow = ({ label, children }: RequestDetailsRowProps) => (
  <div className="flex items-center">
    <div className={`shrink-0 grow-0 basis-1/2 pr-2 ${styles.label}`}>
      <Typography.Text>{label}:</Typography.Text>
    </div>
    <div
      className={`min-w-0 shrink grow ${styles.value}`}
      data-testid={`request-detail-value-${label}`}
    >
      {children}
    </div>
  </div>
);

export default RequestDetailsRow;
