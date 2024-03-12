import { h } from "preact";
import { useDisclosure } from "../../lib/hooks";
import type { I18n } from "../../lib/i18n";
import {
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
} from "../../lib/tcf/types";

const ArrowDown = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none">
    <path
      fill="#2D3748"
      d="m12 13.172 4.95-4.95 1.414 1.414L12 16 5.636 9.636 7.05 8.222l4.95 4.95Z"
    />
  </svg>
);

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
      <div key={title} className="fides-notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          {...getButtonProps()}
          className="fides-notice-toggle-trigger"
        >
          {title}
          <ArrowDown />
        </span>
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
                <li>
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
