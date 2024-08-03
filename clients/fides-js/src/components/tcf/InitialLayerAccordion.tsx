import { h } from "preact";

import { useDisclosure } from "../../lib/hooks";
import type { I18n } from "../../lib/i18n";
import {
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
} from "../../lib/tcf/types";

const InitialLayerAccordion = ({
  i18n,
  title,
  description,
  purposes,
}: {
  i18n: I18n;
  title: string;
  description: string;
  purposes?: Array<
    TCFPurposeConsentRecord | TCFPurposeLegitimateInterestsRecord
  >;
}) => {
  const { isOpen, getButtonProps, getDisclosureProps, onToggle } =
    useDisclosure({
      id: title,
    });

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.code === "Space" || event.code === "Enter") {
      onToggle();
    }
  };

  return (
    <div
      className={
        isOpen
          ? "fides-notice-toggle fides-notice-toggle-expanded"
          : "fides-notice-toggle"
      }
    >
      <div
        key={title}
        className="fides-notice-toggle-title"
        role="button"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        {...getButtonProps()}
      >
        {title}
        <span className="fides-notice-toggle-trigger" />
      </div>
      <div {...getDisclosureProps()}>
        <div>{description}</div>
        {purposes?.length ? (
          <div className="fides-tcf-purpose-vendor fides-background-dark">
            <div className="fides-tcf-purpose-vendor-title fides-tcf-toggle-content">
              {i18n.t("static.tcf.purposes")}
            </div>
            <ul className="fides-tcf-purpose-vendor-list fides-tcf-toggle-content">
              {purposes.map((purpose) => (
                <li key={purpose.id}>
                  {i18n.t(`exp.tcf.purposes.${purpose.id}.name`)}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default InitialLayerAccordion;
