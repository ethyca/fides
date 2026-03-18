import { DatasetNodeHoverStatus } from "../context/DatasetTreeHoverContext";
import styles from "./DatasetNode.module.scss";

export const getNodeHoverClass = (
  status: DatasetNodeHoverStatus,
  options?: { isProtected?: boolean },
): string => {
  if (options?.isProtected) {
    return styles["button--protected"] || "";
  }
  switch (status) {
    case DatasetNodeHoverStatus.ACTIVE_HOVER:
      return styles["button--hover"] || "";
    case DatasetNodeHoverStatus.PARENT_OF_HOVER:
      return styles["button--parent-hover"] || "";
    case DatasetNodeHoverStatus.INACTIVE:
      return styles["button--inactive"] || "";
    default:
      return "";
  }
};
