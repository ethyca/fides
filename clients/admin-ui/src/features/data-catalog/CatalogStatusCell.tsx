import ResultStatusBadge from "~/features/common/ResultStatusBadge";
import { CatalogResourceStatus } from "~/features/data-catalog/utils";

const STATUS_COLOR_MAP: Record<CatalogResourceStatus, string> = {
  [CatalogResourceStatus.ATTENTION_REQUIRED]: "red",
  [CatalogResourceStatus.APPROVED]: "green",
  [CatalogResourceStatus.IN_REVIEW]: "yellow",
  [CatalogResourceStatus.CLASSIFYING]: "blue",
};

const CatalogStatusCell = ({ status }: { status: CatalogResourceStatus }) => {
  return (
    <ResultStatusBadge colorScheme={STATUS_COLOR_MAP[status]}>
      {status}
    </ResultStatusBadge>
  );
};

export default CatalogStatusCell;
