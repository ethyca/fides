import { BadgeCellExpandable } from "~/features/common/table/v2/cells";

const SystemResourceTagsCell = ({
  tags,
}: {
  tags: Record<string, string> | null | undefined;
}) => {
  if (!tags || Object.keys(tags).length === 0) {
    return null;
  }
  const values = Object.entries(tags).map(([k, v]) => ({
    label: `${k}: ${v}`,
    key: `${k}:${v}`,
  }));
  return <BadgeCellExpandable values={values} />;
};

export default SystemResourceTagsCell;
