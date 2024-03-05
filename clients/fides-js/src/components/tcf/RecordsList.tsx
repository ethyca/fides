import { VNode, h } from "preact";
import DataUseToggle from "../DataUseToggle";

interface Item {
  id: string | number;
  name?: string;
}

interface Props<T extends Item> {
  items: T[];
  title: string;
  enabledIds: string[];
  renderToggleChild: (item: T) => VNode;
  onToggle: (payload: string[]) => void;
  renderBadgeLabel?: (item: T) => string | undefined;
  hideToggles?: boolean;
}

const RecordsList = <T extends Item>({
  items,
  title,
  enabledIds,
  renderToggleChild,
  renderBadgeLabel,
  onToggle,
  hideToggles,
}: Props<T>) => {
  if (items.length === 0) {
    return null;
  }

  const handleToggle = (item: T) => {
    const purposeId = `${item.id}`;
    if (enabledIds.indexOf(purposeId) !== -1) {
      onToggle(enabledIds.filter((e) => e !== purposeId));
    } else {
      onToggle([...enabledIds, purposeId]);
    }
  };

  return (
    <div data-testid={`records-list-${title}`}>
      <div className="fides-record-header">{title}</div>
      {items.map((item) => (
        <DataUseToggle
          title={item.name}
          noticeKey={`${item.id}`}
          onToggle={() => {
            handleToggle(item);
          }}
          checked={enabledIds.indexOf(`${item.id}`) !== -1}
          badge={renderBadgeLabel ? renderBadgeLabel(item) : undefined}
          includeToggle={!hideToggles}
        >
          {renderToggleChild(item)}
        </DataUseToggle>
      ))}
    </div>
  );
};

export default RecordsList;
