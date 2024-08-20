import { h } from "preact";

interface TCFBannerSupplementalProps {
  purposes?: string[];
}

export const TCFBannerSupplemental = ({
  purposes,
}: TCFBannerSupplementalProps) => {
  if (!purposes?.length) {
    return null;
  }
  return (
    <div
      id="fides-tcf-banner-inner"
      className="fides-banner__supplemental fides-banner__col"
    >
      <div className="fides-banner-heading">
        <h2 id="fides-banner-subtitle" className="fides-banner-title">
          We use data for the following purposes
        </h2>
      </div>
      <div className="fides-banner__content">
        <ul className="fides-banner__purpose-list">
          {purposes.map((purpose) => (
            <li key={purpose} className="fides-banner__purpose-item">
              {purpose}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
