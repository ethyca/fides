import { h } from "preact";

import { useI18n } from "../../lib/i18n/i18n-context";

interface TCFBannerSupplementalProps {
  purposes: string[] | undefined;
  customPurposes: string[] | undefined;
}

export const TCFBannerSupplemental = ({
  purposes,
  customPurposes,
}: TCFBannerSupplementalProps) => {
  const { i18n } = useI18n();
  if (!purposes?.length) {
    return null;
  }
  return (
    <div
      id="fides-tcf-banner-inner"
      data-testid="fides-tcf-banner-supplemental"
      className="fides-banner__supplemental fides-banner__col"
    >
      {!!i18n.t("exp.purpose_header") &&
        i18n.t("exp.purpose_header") !== "exp.purpose_header" && (
          <div className="fides-banner-heading">
            <h2
              id="fides-banner-subtitle"
              data-testid="fides-banner-subtitle"
              className="fides-banner-title"
            >
              {i18n.t("exp.purpose_header")}
            </h2>
          </div>
        )}
      <div className="fides-banner__content">
        <ul className="fides-banner__purpose-list">
          {customPurposes?.map((purpose) => (
            <li key={purpose} className="fides-banner__purpose-item">
              {purpose}
            </li>
          ))}
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
