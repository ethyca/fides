import type { AttributionOptions } from "fides-js";

import styles from "./AttributionLink.module.scss";
import { EthycaLogoSvg } from "./EthycaLogoSvg";

export const AttributionLink = ({
  attribution,
}: {
  attribution: AttributionOptions;
}) => (
  <div className={styles.wrapper} data-testid="attribution-link">
    <a
      className={styles.link}
      href={attribution.destinationUrl}
      target="_blank"
      rel={`noopener noreferrer${attribution.nofollow ? " nofollow" : ""}`}
    >
      {attribution.anchorText}
      <EthycaLogoSvg size={11} />
    </a>
  </div>
);
