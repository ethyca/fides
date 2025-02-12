import { BadgeCell } from "~/features/common/table/v2";
import { CatalogResourceStatus } from "~/features/data-catalog/utils";

const STATUS_COLOR_MAP: Record<CatalogResourceStatus, string> = {
  [CatalogResourceStatus.ATTENTION_REQUIRED]: "red",
  [CatalogResourceStatus.APPROVED]: "green",
  [CatalogResourceStatus.IN_REVIEW]: "yellow",
  [CatalogResourceStatus.CLASSIFYING]: "blue",
  [CatalogResourceStatus.NONE]: "gray",
};

const CatalogStatusBadgeCell = ({
  status,
}: {
  status: CatalogResourceStatus;
}) => {
  return <BadgeCell colorScheme={STATUS_COLOR_MAP[status]} value={status} />;
};

export default CatalogStatusBadgeCell;
