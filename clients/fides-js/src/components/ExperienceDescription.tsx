import { h } from "preact";
import { useContext } from "preact/hooks";

import { VendorButtonContext } from "../lib/tcf/vendor-button-context";

const VENDOR_COUNT_LINK = "__VENDOR_COUNT_LINK__";

const ExperienceDescription = ({
  description,
  onVendorPageClick,
  allowHTMLDescription = false,
}: {
  description: string | undefined;
  onVendorPageClick?: () => void;
  allowHTMLDescription?: boolean | null;
}) => {
  let vendorCount = 0;
  const context = useContext(VendorButtonContext);
  if (context?.vendorCount) {
    vendorCount = context.vendorCount;
  }

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
        {!onVendorPageClick && !!vendorCount && (
          <span className="fides-vendor-count">{vendorCount}</span>
        )}
        {onVendorPageClick && !!vendorCount && (
          <button
            type="button"
            className="fides-link-button fides-vendor-count"
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
