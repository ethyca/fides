import { ComponentChildren, Fragment, h, VNode } from "preact";
import type { HTMLAttributes } from "preact/compat";

import { getConsentContext } from "../lib/consent-context";
import type { I18n } from "../lib/i18n";
import ExperienceDescription from "./ExperienceDescription";
import GpcInfo from "./GpcInfo";

export interface ConsentContentProps {
  titleProps: HTMLAttributes<HTMLHeadingElement>;
  i18n: I18n;
  children: ComponentChildren;
  className?: string;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode;
}

const ConsentModal = ({
  titleProps,
  className,
  i18n,
  renderModalFooter,
  children,
  onVendorPageClick,
}: ConsentContentProps) => {
  const title = i18n.t("exp.title");
  const description = i18n.t("exp.description");
  const showGpcInfo = getConsentContext().globalPrivacyControl;
  const gpcTitle = i18n.t("static.gpc.title");
  const gpcDescription = i18n.t("static.gpc.description");

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
            {...titleProps}
            className="fides-modal-title"
          >
            {title}
          </div>
          <p
            data-testid="fides-modal-description"
            className="fides-modal-description"
          >
            <ExperienceDescription
              onVendorPageClick={onVendorPageClick}
              description={description}
              allowHTMLDescription={window.Fides?.options?.allowHTMLDescription}
            />
          </p>
          {showGpcInfo && (
            <GpcInfo title={gpcTitle} description={gpcDescription} />
          )}
          {children}
        </div>
      </div>
      <div className="fides-modal-footer">{renderModalFooter()}</div>
    </Fragment>
  );
};

export default ConsentModal;
