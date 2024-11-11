import { h } from "preact";

import EthycaLogo from "./EthycaLogo";

const BrandLink = ({ url }: { url: string }) => (
  <div
    id="fides-brand-link"
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <a
      href={url}
      style={{
        color: "#a0aec0",
        textDecoration: "none",
        fontSize: "8px",
        display: "flex",
        alignItems: "center",
        gap: "4px",
      }}
      rel="noopener noreferrer"
      target="_blank"
      className="fides-brand"
    >
      Powered by
      <EthycaLogo />
    </a>
  </div>
);

export default BrandLink;
