import { h } from "preact";

const TEXT_TO_LINK = "vendors page.";

const ExperienceDescription = ({
  description,
  onVendorPageClick,
}: {
  description: string | undefined;
  onVendorPageClick?: () => void;
}) => {
  if (!description) {
    return null;
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
