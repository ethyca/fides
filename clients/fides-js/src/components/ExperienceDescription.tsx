/* eslint-disable no-template-curly-in-string */
import { h } from "preact";

import { useVendorButton } from "../lib/tcf/vendor-button-context";

const VENDOR_COUNT_LINK = "${VENDOR_COUNT_LINK}";

const ExperienceDescription = ({
  description,
  onVendorPageClick,
  allowHTMLDescription = false,
}: {
  description: string | undefined;
  onVendorPageClick?: () => void;
  allowHTMLDescription?: boolean | null;
}) => {
  const { vendorCount } = useVendorButton();

  if (!description) {
    return null;
  }

  // If allowHTMLDescription is true, render rich HTML content
  // NOTE: We sanitize these descriptions server-side when configuring the
  // PrivacyExperience, so it's safe to trust these
  if (allowHTMLDescription) {
    return (
      <div
        className="fides-html-description"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: description }}
      />
    );
  }

  // Swap out reference to "vendors page" with a button that can go to the vendor page
  if (description.includes(VENDOR_COUNT_LINK)) {
    const parts = description.split(VENDOR_COUNT_LINK);
    return (
      <div>
        {parts[0]}
        {onVendorPageClick && vendorCount && (
          <button
            type="button"
            className="fides-link-button"
            onClick={onVendorPageClick}
          >
            {vendorCount}
          </button>
        )}
        {parts[1]}
      </div>
    );
  }

  return <div>{description}</div>;
};

export default ExperienceDescription;
