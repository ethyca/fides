import { Tooltip } from "fidesui";

import ResultStatusBadge from "~/features/common/ResultStatusBadge";
import {
  DatasetLifecycleStatusEnum,
  DatasetLifecycleStatusResult,
} from "~/features/dataset-lifecycle/types";

const STATUS_COLOR_MAP: Record<DatasetLifecycleStatusEnum, string> = {
  [DatasetLifecycleStatusEnum.ADDED]: "green",
  [DatasetLifecycleStatusEnum.IN_PROGRESS]: "orange",
  [DatasetLifecycleStatusEnum.ATTENTION]: "red",
};

const StatusBadgeCell = ({
  statusResult: { status, detail },
}: {
  statusResult: DatasetLifecycleStatusResult;
}) => {
  return (
    <Tooltip label={detail}>
      <ResultStatusBadge colorScheme={STATUS_COLOR_MAP[status]}>
        {status}
      </ResultStatusBadge>
    </Tooltip>
  );
};

export default StatusBadgeCell;
