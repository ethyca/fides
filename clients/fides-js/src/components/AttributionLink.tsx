import type { AttributionOptions } from "../lib/consent-types";
import EthycaLogo from "./EthycaLogo";

interface AttributionLinkProps {
  attribution: AttributionOptions;
}

export const AttributionLink = ({ attribution }: AttributionLinkProps) => (
  <a
    href={attribution.destinationUrl}
    target="_blank"
    rel={`noopener noreferrer${attribution.nofollow ? " nofollow" : ""}`}
    className="fides-attribution"
  >
    {attribution.anchorText}
    <EthycaLogo />
  </a>
);
