import { Fragment, h } from "preact";
import { useContext, useEffect, useState } from "preact/hooks";

import { VendorButtonContext } from "../lib/tcf/vendor-button-context";
import { stripHtml } from "../lib/ui-utils";

const VENDOR_COUNT_LINK = "__VENDOR_COUNT_LINK__";

const renderString = (string: string, allowHTMLDescription: boolean | null) => {
  // If allowHTMLDescription is true, render rich HTML content
  // NOTE: We sanitize these descriptions server-side when configuring the
  // PrivacyExperience, so it's safe to trust these
  return allowHTMLDescription ? (
    <span
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: string.trim() }}
    />
  ) : (
    stripHtml(string).trim()
  );
};

const ExperienceDescription = ({
  description,
  onVendorPageClick,
  allowHTMLDescription = false,
}: {
  description: string | undefined;
  onVendorPageClick?: () => void;
  allowHTMLDescription?: boolean | null;
}) => {
  const [renderedDescription, setRenderedDescription] =
    useState<(string | h.JSX.Element)[]>();
  let vendorCount = 0;
  const context = useContext(VendorButtonContext);
  if (context?.vendorCount) {
    vendorCount = context.vendorCount;
  }

  useEffect(() => {
    // Swap out reference to "vendors page" with a button that can go to the vendor page
    if (description) {
      if (description.includes(VENDOR_COUNT_LINK) && onVendorPageClick) {
        const parts: (string | h.JSX.Element)[] =
          description.split(VENDOR_COUNT_LINK);
        // inject vendor count button each time it appeared in the description
        for (let i = 1; i < parts.length; i += 2) {
          parts.splice(
            i,
            0,
            <Fragment>
              {" "}
              <button
                type="button"
                className="fides-link-button fides-vendor-count"
                onClick={onVendorPageClick}
              >
                {vendorCount}
              </button>{" "}
            </Fragment>,
          );
        }

        const renderedParts = parts.map((part) => {
          if (typeof part === "string") {
            return renderString(part, allowHTMLDescription);
          }
          return part;
        });
        setRenderedDescription(renderedParts);
      } else {
        setRenderedDescription([
          renderString(description, allowHTMLDescription),
        ]);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [description, onVendorPageClick]);

  if (!description) {
    return null;
  }

  return <div>{renderedDescription}</div>;
};

export default ExperienceDescription;
