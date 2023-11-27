import { h } from "preact";

import { EmbeddedVendor } from "../../lib/tcf/types";

import PagingButtons, { usePaging } from "../PagingButtons";

const EmbeddedVendorList = ({
  vendors: totalVendors,
}: {
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
        Vendors we use for this purpose
        <span>{totalVendors.length} vendor(s)</span>
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
