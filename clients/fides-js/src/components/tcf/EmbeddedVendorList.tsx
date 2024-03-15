import { h } from "preact";

import { I18n } from "../../lib/i18n";
import { EmbeddedVendor } from "../../lib/tcf/types";

import PagingButtons, { usePaging } from "../PagingButtons";

const EmbeddedVendorList = ({
  i18n,
  vendors: totalVendors,
}: {
  i18n: I18n;
  vendors: EmbeddedVendor[];
}) => {
  const {
    activeChunk: vendors,
    totalPages,
    ...paging
  } = usePaging(totalVendors);

  if (!vendors.length) {
    return null;
  }

  return (
    <p className="fides-tcf-toggle-content fides-background-dark fides-tcf-purpose-vendor">
      <span className="fides-tcf-purpose-vendor-title">
        {i18n.t("static.tcf.vendors")}
        <span>
          {totalVendors.length} {i18n.t("static.tcf.vendors_count")}
        </span>
      </span>
      <ul className="fides-tcf-purpose-vendor-list">
        {vendors.map((v) => (
          <li>{v.name}</li>
        ))}
      </ul>
      {totalPages > 1 ? <PagingButtons {...paging} /> : null}
    </p>
  );
};

export default EmbeddedVendorList;
