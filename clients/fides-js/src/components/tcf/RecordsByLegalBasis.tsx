import { VNode, h } from "preact";
import { useMemo, useState } from "preact/hooks";
import DataUseToggle from "../DataUseToggle";
import { EnabledIds, LegalBasisEnum } from "../../lib/tcf/types";
import type { UpdateEnabledIds } from "./TcfOverlay";
import FilterButtons from "./FilterButtons";

const FILTERS = [
  { label: "Consent", value: LegalBasisEnum.CONSENT },
  { label: "Legitimate interest", value: LegalBasisEnum.LEGITIMATE_INTERESTS },
];
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

const RecordsByLegalBasis = <T extends Item>({
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
  // const toggleAllId = `all-${title}`;
  // const toggleAllConsentId = `${toggleAllId}-consent`;

  // const { allConsentChecked, allLegintChecked } = useMemo(() => {
  //   const consentIds = items.filter((i) => i.isConsent).map((i) => `${i.id}`);
  //   const legintIds = items.filter((i) => i.isLegint).map((i) => `${i.id}`);

  //   const consentChecked = consentIds.every(
  //     (id) => enabledConsentIds.indexOf(id) !== -1
  //   );
  //   const legintChecked = legintIds.every(
  //     (id) => enabledLegintIds.indexOf(id) !== -1
  //   );
  //   return {
  //     allConsentChecked: consentChecked,
  //     allLegintChecked: legintChecked,
  //   };
  // }, [items, enabledConsentIds, enabledLegintIds]);

  // const { hasConsentItems, hasLegintItems } = useMemo(
  //   () => ({
  //     hasConsentItems: !!items.filter((i) => i.isConsent).length,
  //     hasLegintItems: !!items.filter((i) => i.isLegint).length,
  //   }),
  //   [items]
  // );

  const [activeLegalBasis, setActiveLegalBasis] = useState(FILTERS[0].value);

  const records = useMemo(() => {
    if (activeLegalBasis === LegalBasisEnum.CONSENT) {
      return items.filter((i) => i.isConsent);
    }
    return items.filter((i) => i.isLegint);
  }, [activeLegalBasis, items]);

  const enabledIds = useMemo(
    () =>
      activeLegalBasis === LegalBasisEnum.CONSENT
        ? enabledConsentIds
        : enabledLegintIds,
    [activeLegalBasis, enabledConsentIds, enabledLegintIds]
  );

  // const handleToggleAll = (legalBasis: LegalBasisEnum) => {
  //   const isConsent = legalBasis === LegalBasisEnum.CONSENT;
  //   const modelType = isConsent ? consentModelType : legintModelType;
  //   const allChecked = isConsent ? allConsentChecked : allLegintChecked;
  //   if (allChecked) {
  //     onToggle({ newEnabledIds: [], modelType });
  //   } else {
  //     const allItems = isConsent
  //       ? items.filter((i) => i.isConsent)
  //       : items.filter((i) => i.isLegint);
  //     onToggle({
  //       newEnabledIds: allItems.map((i) => `${i.id}`),
  //       modelType,
  //     });
  //   }
  // };

  const handleToggleIndividual = (item: T) => {
    const isConsent = activeLegalBasis === LegalBasisEnum.CONSENT;
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
      <FilterButtons<(typeof FILTERS)[0]>
        filters={FILTERS}
        onChange={(f) => setActiveLegalBasis(f.value)}
      />
      <div className="fides-record-header">{title}</div>
      {records.map((item) => (
        <DataUseToggle
          dataUse={{
            key: `${item.id}`,
            name: item.name,
          }}
          onToggle={() => {
            handleToggleIndividual(item);
          }}
          checked={enabledIds.indexOf(`${item.id}`) !== -1}
          badge={renderBadgeLabel ? renderBadgeLabel(item) : undefined}
        >
          {renderToggleChild(item)}
        </DataUseToggle>
      ))}
    </div>
  );
};

export default RecordsByLegalBasis;
