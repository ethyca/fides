import { h } from "preact";

import { useMemo } from "preact/hooks";
import { EnabledIds } from "../../lib/tcf/types";

const BUTTON_CLASSNAME = "fides-link-button fides-primary-text-color";

interface Item {
  id: string | number;
}

interface Props<T> {
  enabledIds: EnabledIds;
  onChange: (payload: EnabledIds) => void;
  modelTypeMappings: Partial<Record<keyof EnabledIds, T[]>>;
}

const AllOnOffButtons = <T extends Item>({
  enabledIds,
  modelTypeMappings,
  onChange,
}: Props<T>) => {
  const handleAllOff = () => {
    const updated = { ...enabledIds };
    const modelTypes = Object.keys(modelTypeMappings) as Array<
      keyof EnabledIds
    >;
    modelTypes.forEach((modelType) => {
      updated[modelType] = [];
    });
    onChange(updated);
  };

  const handleAllOn = () => {
    const updated = { ...enabledIds };
    Object.entries(modelTypeMappings).forEach(([modelType, items]) => {
      updated[modelType as keyof EnabledIds] = items.map((i) => `${i.id}`);
    });
    onChange(updated);
  };

  const isEmpty = useMemo(
    () =>
      Object.values(modelTypeMappings).every(
        (recordList) => recordList.length === 0
      ),
    [modelTypeMappings]
  );

  if (isEmpty) {
    return null;
  }

  return (
    <div className="fides-all-on-off-buttons">
      <button
        type="button"
        className={`${BUTTON_CLASSNAME} fides-all-on-button`}
        onClick={handleAllOn}
      >
        All on
      </button>
      <button type="button" className={BUTTON_CLASSNAME} onClick={handleAllOff}>
        All off
      </button>
    </div>
  );
};

export default AllOnOffButtons;
