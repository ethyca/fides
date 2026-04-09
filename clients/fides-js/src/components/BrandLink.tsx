import { EthycaLogo } from "./EthycaLogo";

export const BrandLink = () => (
  <div className="fides-brand">
    <a
      href="https://ethyca.com/?utm_source=fides_consent&utm_medium=referral&utm_campaign=cmp_backlinks&utm_term=home"
      target="_blank"
      rel="noopener noreferrer"
      className="fides-brand-link"
    >
      Powered by
      <EthycaLogo />
    </a>
  </div>
);
