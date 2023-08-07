import { h } from "preact";
import { useState } from "preact/hooks";
import { EmbeddedLineItem, TCFVendorRecord } from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";
import FilterButtons from "./FilterButtons";

const FILTERS = [{ name: "All vendors" }, { name: "GVL vendors" }];

const VendorDetails = ({
  label,
  lineItems,
}: {
  label: string;
  lineItems: EmbeddedLineItem[] | undefined;
}) => {
  if (!lineItems || lineItems.length === 0) {
    return null;
  }

  return (
    <p className="fides-tcf-purpose-vendor fides-tcf-toggle-content fides-background-dark">
      <span className="fides-tcf-purpose-vendor-title">{label}</span>
      <ul className="fides-tcf-purpose-vendor-list">
        {lineItems.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </p>
  );
};

const TcfVendors = ({
  allVendors,
  enabledIds,
  onChange,
}: {
  allVendors: PrivacyExperience["tcf_vendors"];
  enabledIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => {
  const [isFiltered, setIsFiltered] = useState(false);

  if (!allVendors || allVendors.length === 0) {
    // TODO: empty state?
    return null;
  }

  const handleToggle = (vendor: TCFVendorRecord) => {
    if (enabledIds.indexOf(vendor.id) !== -1) {
      onChange({
        newEnabledIds: enabledIds.filter((e) => e !== vendor.id),
        modelType: "vendors",
      });
    } else {
      onChange({
        newEnabledIds: [...enabledIds, vendor.id],
        modelType: "vendors",
      });
    }
  };

  const handleFilter = (index: number) => {
    if (index === 0) {
      setIsFiltered(false);
    } else {
      setIsFiltered(true);
    }
  };

  const vendorsToDisplay = isFiltered
    ? allVendors.filter((v) => v.is_gvl)
    : allVendors;

  return (
    <div>
      <FilterButtons filters={FILTERS} onChange={handleFilter} />
      {vendorsToDisplay.map((vendor) => (
        <DataUseToggle
          dataUse={{ key: vendor.id, name: vendor.name }}
          onToggle={() => {
            handleToggle(vendor);
          }}
          checked={enabledIds.indexOf(vendor.id) !== -1}
          badge={vendor.is_gvl ? "GVL" : undefined}
        >
          <div>
            <p>{vendor.description}</p>
            <VendorDetails label="Purposes" lineItems={vendor.purposes} />
            <VendorDetails
              label="Special purposes"
              lineItems={vendor.special_purposes}
            />
            <VendorDetails label="Features" lineItems={vendor.features} />
            <VendorDetails
              label="Special features"
              lineItems={vendor.special_features}
            />
          </div>
        </DataUseToggle>
      ))}
    </div>
  );
};

export default TcfVendors;
