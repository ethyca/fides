import { ComponentChildren, Fragment, VNode } from "preact";
import type { HTMLAttributes } from "preact/compat";

import { getConsentContext } from "../lib/consent-context";
import { useI18n } from "../lib/i18n/i18n-context";
import ExperienceDescription from "./ExperienceDescription";
import GpcInfo from "./GpcInfo";

export interface ConsentContentProps {
  titleProps: HTMLAttributes<HTMLHeadingElement>;
  children: ComponentChildren;
  className?: string;
  onVendorPageClick?: () => void;
  renderModalFooter: () => VNode | null;
  headerContent: {
    title: string;
    description: string;
  };
  isVendorAssetDisclosureView?: boolean;
}

const ConsentContent = ({
  titleProps,
  className,
  renderModalFooter,
  children,
  onVendorPageClick,
  headerContent,
  isVendorAssetDisclosureView,
}: ConsentContentProps) => {
  const { title, description } = headerContent;
  const { i18n } = useI18n();
  const gpcEnabled = getConsentContext().globalPrivacyControl;
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
            {...titleProps} // adds role, aria-level, id
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
          {!isVendorAssetDisclosureView && gpcEnabled && (
            <GpcInfo title={gpcTitle} description={gpcDescription} />
          )}
          {children}
        </div>
      </div>
      <div className="fides-modal-footer">{renderModalFooter()}</div>
    </Fragment>
  );
};

export default ConsentContent;
