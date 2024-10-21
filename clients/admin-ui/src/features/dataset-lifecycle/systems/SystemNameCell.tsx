import { DefaultCell } from "~/features/common/table/v2";

const SystemNameCell = ({
  value,
  clickable,
}: {
  value: string;
  clickable?: boolean;
}) => (
  <DefaultCell value={value} fontWeight={clickable ? "semibold" : "normal"} />
);

export default SystemNameCell;
