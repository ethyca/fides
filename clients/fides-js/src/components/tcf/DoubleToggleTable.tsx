/** This isn't a table _yet_, but it is aspirationally named.
 * We should probably convert it to a table at some point fides#4190 */

import { VNode, h } from "preact";
import { useMemo } from "react";
import DataUseToggle from "../DataUseToggle";
import Toggle from "../Toggle";
import { EnabledIds, LegalBasisEnum } from "../../lib/tcf/types";
import type { UpdateEnabledIds } from "./TcfOverlay";

interface Item {
  id: string | number;
  name?: string;
  isConsent: boolean;
  isLegint: boolean;
}

interface Props<T extends Item> {
  items: T[];
  title: string;
  enabledConsentIds: string[];
  enabledLegintIds: string[];
  renderToggleChild: (item: T) => VNode;
  onToggle: (payload: UpdateEnabledIds) => void;
  renderBadgeLabel?: (item: T) => string | undefined;
  consentModelType: keyof EnabledIds;
  legintModelType: keyof EnabledIds;
}

const DoubleToggleTable = <T extends Item>({
  items,
  title,
  enabledConsentIds,
  enabledLegintIds,
  renderToggleChild,
  renderBadgeLabel,
  onToggle,
  consentModelType,
  legintModelType,
}: Props<T>) => {
  const toggleAllId = `all-${title}`;
  const toggleAllConsentId = `${toggleAllId}-consent`;

  const { allConsentChecked, allLegintChecked } = useMemo(() => {
    const consentIds = items.filter((i) => i.isConsent).map((i) => `${i.id}`);
    const legintIds = items.filter((i) => i.isLegint).map((i) => `${i.id}`);

    const consentChecked = consentIds.every(
      (id) => enabledConsentIds.indexOf(id) !== -1
    );
    const legintChecked = legintIds.every(
      (id) => enabledLegintIds.indexOf(id) !== -1
    );
    return {
      allConsentChecked: consentChecked,
      allLegintChecked: legintChecked,
    };
  }, [items, enabledConsentIds, enabledLegintIds]);

  const { hasConsentItems, hasLegintItems } = useMemo(
    () => ({
      hasConsentItems: !!items.filter((i) => i.isConsent).length,
      hasLegintItems: !!items.filter((i) => i.isLegint).length,
    }),
    [items]
  );

  const handleToggleAll = (legalBasis: LegalBasisEnum) => {
    const isConsent = legalBasis === LegalBasisEnum.CONSENT;
    const modelType = isConsent ? consentModelType : legintModelType;
    const allChecked = isConsent ? allConsentChecked : allLegintChecked;
    if (allChecked) {
      onToggle({ newEnabledIds: [], modelType });
    } else {
      const allItems = isConsent
        ? items.filter((i) => i.isConsent)
        : items.filter((i) => i.isLegint);
      onToggle({
        newEnabledIds: allItems.map((i) => `${i.id}`),
        modelType,
      });
    }
  };

  const handleToggleIndividual = (item: T, legalBasis: LegalBasisEnum) => {
    const isConsent = legalBasis === LegalBasisEnum.CONSENT;
    const enabledIds = isConsent ? enabledConsentIds : enabledLegintIds;
    const modelType = isConsent ? consentModelType : legintModelType;
    const purposeId = `${item.id}`;
    if (enabledIds.indexOf(purposeId) !== -1) {
      onToggle({
        newEnabledIds: enabledIds.filter((e) => e !== purposeId),
        modelType,
      });
    } else {
      onToggle({
        newEnabledIds: [...enabledIds, purposeId],
        modelType,
      });
    }
  };

  return (
    <div>
      {/* DEFER: ideally we use a table object, but then DataUseToggles would need to be reworked
      or we would need a separate component. */}
      <div className="fides-legal-basis-labels">
        <span className="fides-margin-right">Legitimate interest</span>
        <span>Consent</span>
      </div>
      <DataUseToggle
        dataUse={{
          key: title,
          name: title,
        }}
        onToggle={() => {
          handleToggleAll(LegalBasisEnum.LEGITIMATE_INTERESTS);
        }}
        isHeader
        checked={allLegintChecked}
        secondToggle={
          <div style={{ display: "flex", marginLeft: "16px" }}>
            {hasConsentItems ? (
              <Toggle
                name={toggleAllConsentId}
                id={toggleAllConsentId}
                checked={allConsentChecked}
                onChange={() => handleToggleAll(LegalBasisEnum.CONSENT)}
              />
            ) : null}
          </div>
        }
        includeToggle={hasLegintItems}
      />
      {items.map((item) => (
        <DataUseToggle
          dataUse={{
            key: `${item.id}-legint`,
            name: item.name,
          }}
          onToggle={() => {
            handleToggleIndividual(item, LegalBasisEnum.LEGITIMATE_INTERESTS);
          }}
          checked={enabledLegintIds.indexOf(`${item.id}`) !== -1}
          badge={renderBadgeLabel ? renderBadgeLabel(item) : undefined}
          secondToggle={
            <div
              style={{ display: "flex", marginLeft: "16px", minWidth: "95px" }}
            >
              {item.isConsent ? (
                <Toggle
                  name={`${item.name}-consent`}
                  id={`${item.id}-consent`}
                  checked={enabledConsentIds.indexOf(`${item.id}`) !== -1}
                  onChange={() =>
                    handleToggleIndividual(item, LegalBasisEnum.CONSENT)
                  }
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
