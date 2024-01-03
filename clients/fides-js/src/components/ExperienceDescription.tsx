import { h } from "preact";

const TEXT_TO_LINK = "vendors page.";

const ExperienceDescription = ({
  description,
  onVendorPageClick,
  allowHTMLDescription = false,
}: {
  description: string | undefined;
  onVendorPageClick?: () => void;
  allowHTMLDescription?: boolean | null;
}) => {
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
  if (
    onVendorPageClick &&
    (description.endsWith(TEXT_TO_LINK) ||
      description.endsWith(`${TEXT_TO_LINK}\n`))
  ) {
    const firstPart = description.split(TEXT_TO_LINK)[0];
    return (
      <div>
        {firstPart}{" "}
        <button
          type="button"
          className="fides-link-button"
          onClick={onVendorPageClick}
        >
          {TEXT_TO_LINK}
        </button>
      </div>
    );
  }

  return <div>{description}</div>;
};

export default ExperienceDescription;
