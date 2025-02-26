import { h } from "preact";

import EthycaLogo from "./EthycaLogo";

const BrandLink = () => (
  <div className="fides-brand">
    <a
      href="https://ethyca.com/"
      target="_blank"
      rel="noopener noreferrer"
      className="fides-brand-link"
    >
      Powered by
      <EthycaLogo />
    </a>
  </div>
);

export default BrandLink;
