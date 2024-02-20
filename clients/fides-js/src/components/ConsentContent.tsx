import { ComponentChildren, VNode, h, Fragment } from "preact";
import type { HTMLAttributes } from "react";

import { getConsentContext } from "../lib/consent-context";
import type { I18n } from "../lib/i18n";

import GpcInfo from "./GpcInfo";
import ExperienceDescription from "./ExperienceDescription";

export interface ConsentContentProps {
  title: HTMLAttributes<HTMLHeadingElement>;
  i18n: I18n;
  children: ComponentChildren;
  className?: string;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode;
}

const ConsentModal = ({
  title,
  className,
  i18n,
  renderModalFooter,
  children,
  onVendorPageClick,
}: ConsentContentProps) => {
  const showGpcBadge = getConsentContext().globalPrivacyControl;

  return (
    <Fragment>
      <div
        data-testid="consent-content"
        id="fides-consent-content"
        className={className}
      >
        <div className="fides-modal-body">
          <div
            data-testid="fides-modal-title"
            {...title}
            className="fides-modal-title"
          >
            {i18n.t("experience.title")}
          </div>
          <p
            data-testid="fides-modal-description"
            className="fides-modal-description"
          >
            <ExperienceDescription
              onVendorPageClick={onVendorPageClick}
              description={i18n.t("experience.description")}
              allowHTMLDescription={window.Fides?.options?.allowHTMLDescription}
            />
          </p>
          {showGpcBadge && <GpcInfo />}
          {children}
        </div>
      </div>
      <div className="fides-modal-footer">{renderModalFooter()}</div>
    </Fragment>
  );
};

export default ConsentModal;
