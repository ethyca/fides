import { BadgeCell } from "~/features/common/table/v2";
import { CatalogResourceStatus } from "~/features/data-catalog/utils";

const STATUS_COLOR_MAP: Record<CatalogResourceStatus, string> = {
  [CatalogResourceStatus.ATTENTION_REQUIRED]: "error",
  [CatalogResourceStatus.APPROVED]: "success",
  [CatalogResourceStatus.IN_REVIEW]: "warning",
  [CatalogResourceStatus.CLASSIFYING]: "info",
  [CatalogResourceStatus.NONE]: "marble",
};

const CatalogStatusBadgeCell = ({
  status,
}: {
  status: CatalogResourceStatus;
}) => {
  return <BadgeCell color={STATUS_COLOR_MAP[status]} value={status} />;
};

export default CatalogStatusBadgeCell;
