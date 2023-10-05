/** This isn't a table _yet_, but it probably should be fides#4190 */

import { VNode, h } from "preact";
import DataUseToggle from "../DataUseToggle";
import Toggle from "../Toggle";

interface Item {
  id: string | number;
  name?: string;
  isConsent: boolean;
  isLegint: boolean;
}

interface Props<T extends Item> {
  items: T[];
  enabledConsentIds: string[];
  enabledLegintIds: string[];
  renderToggleChild: (item: T) => VNode;
  onToggle: (item: T) => void;
  renderBadgeLabel?: (item: T) => string | undefined;
}

const DoubleToggleTable = <T extends Item>({
  items,
  enabledConsentIds,
  enabledLegintIds,
  renderToggleChild,
  renderBadgeLabel,
  onToggle,
}: Props<T>) => {
  console.log({ enabledLegintIds, enabledConsentIds });
  return (
    <div>
      {/* DEFER: ideally we use a table object, but then DataUseToggles would need to be reworked
      or we would need a separate component. */}
      <div className="fides-legal-basis-labels">
        <span className="fides-margin-right">Legitimate interest</span>
        <span>Consent</span>
      </div>
      {items.map((item) => (
        <DataUseToggle
          dataUse={{
            key: `${item.id}-legint`,
            name: item.name,
          }}
          onToggle={() => {
            onToggle(item);
          }}
          checked={enabledLegintIds.indexOf(`${item.id}`) !== -1}
          badge={renderBadgeLabel ? renderBadgeLabel(item) : undefined}
          secondToggle={
            <div style={{ width: "50px", display: "flex", marginLeft: ".2em" }}>
              {item.isConsent ? (
                <Toggle
                  name={`${item.name}-consent`}
                  id={`${item.id}-consent`}
                  checked={enabledConsentIds.indexOf(`${item.id}`) !== -1}
                  onChange={() => onToggle(item)}
                />
              ) : null}
            </div>
          }
          includeToggle={item.isLegint}
        >
          {renderToggleChild(item)}
        </DataUseToggle>
      ))}
    </div>
  );
};

export default DoubleToggleTable;
