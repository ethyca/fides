import { AntColumnsType as ColumnsType } from "fidesui";

import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

export type ExpandableMenu = NonNullable<
  ColumnsType<SystemStagedResourcesAggregateRecord>[number]["menu"]
>;

export const buildExpandCollapseMenu = (
  setExpanded: (value: boolean) => void,
  setVersion: (fn: (prev: number) => number) => void,
): ExpandableMenu => ({
  items: expandCollapseAllMenuItems,
  onClick: (e) => {
    e.domEvent.stopPropagation();
    if (e.key === "expand-all") {
      setExpanded(true);
      setVersion((prev) => prev + 1);
    } else if (e.key === "collapse-all") {
      setExpanded(false);
      setVersion((prev) => prev + 1);
    }
  },
});
