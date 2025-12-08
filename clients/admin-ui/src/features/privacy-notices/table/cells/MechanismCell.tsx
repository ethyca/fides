import { AntTag as Tag } from "fidesui";

import { MECHANISM_MAP } from "~/features/privacy-notices/constants";
import { ConsentMechanism } from "~/types/api";

const MechanismCell = ({ value }: { value: ConsentMechanism }) => {
  const tagLabel = MECHANISM_MAP.get(value) ?? value;

  return (
    <Tag data-testid="status-badge" style={{ textTransform: "uppercase" }}>
      {tagLabel}
    </Tag>
  );
};

export default MechanismCell;
