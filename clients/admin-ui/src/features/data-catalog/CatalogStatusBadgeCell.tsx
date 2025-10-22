import { CUSTOM_TAG_COLOR } from "fidesui";

import { BadgeCell } from "~/features/common/table/v2";
import { CatalogResourceStatus } from "~/features/data-catalog/utils";

const STATUS_COLOR_MAP: Record<CatalogResourceStatus, CUSTOM_TAG_COLOR> = {
  [CatalogResourceStatus.ATTENTION_REQUIRED]: CUSTOM_TAG_COLOR.ERROR,
  [CatalogResourceStatus.APPROVED]: CUSTOM_TAG_COLOR.SUCCESS,
  [CatalogResourceStatus.IN_REVIEW]: CUSTOM_TAG_COLOR.WARNING,
  [CatalogResourceStatus.CLASSIFYING]: CUSTOM_TAG_COLOR.INFO,
  [CatalogResourceStatus.NONE]: CUSTOM_TAG_COLOR.MARBLE,
};

const CatalogStatusBadgeCell = ({
  status,
}: {
  status: CatalogResourceStatus;
}) => {
  return <BadgeCell color={STATUS_COLOR_MAP[status]} value={status} />;
};

export default CatalogStatusBadgeCell;
