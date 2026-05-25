import { Tooltip, Typography } from "fidesui";

const TcfHashDisplay = ({ value }: { value: string | null | undefined }) =>
  value ? (
    <Tooltip title={value}>
      <Typography.Text code className="text-xs">
        {value.slice(0, 8)}
      </Typography.Text>
    </Tooltip>
  ) : (
    <Typography.Text type="secondary" className="text-xs">
      (none)
    </Typography.Text>
  );

export default TcfHashDisplay;
