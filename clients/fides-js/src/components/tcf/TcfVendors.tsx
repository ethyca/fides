import { h } from "preact";
import { useState } from "preact/hooks";
import {
  EmbeddedLineItem,
  EmbeddedPurpose,
  GVLJson,
  TCFVendorRecord,
} from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";
import FilterButtons from "./FilterButtons";
import { vendorIsGvl } from "../../lib/tcf/vendors";
import LegalBasisDropdown, {
  useLegalBasisDropdown,
} from "./LegalBasisDropdown";

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

const PurposeVendorDetails = ({
  purposes,
  specialPurposes,
}: {
  purposes: EmbeddedPurpose[] | undefined;
  specialPurposes: EmbeddedPurpose[] | undefined;
}) => {
  const { filtered, legalBasisFilter, setLegalBasisFilter } =
    useLegalBasisDropdown({
      allPurposes: purposes,
      allSpecialPurposes: specialPurposes,
    });

  const emptyPurposes = purposes ? purposes.length === 0 : true;
  const emptySpecialPurposes = specialPurposes
    ? specialPurposes.length === 0
    : true;

  if (emptyPurposes && emptySpecialPurposes) {
    return null;
  }

  return (
    <div>
      <LegalBasisDropdown
        selected={legalBasisFilter}
        onSelect={(basis) => setLegalBasisFilter(basis)}
      />
      <VendorDetails
        label="Purposes"
        lineItems={filtered.purposes as EmbeddedLineItem[]}
      />
      <VendorDetails
        label="Special purposes"
        lineItems={filtered.specialPurposes as EmbeddedLineItem[]}
      />
    </div>
  );
};

const TcfVendors = ({
  allVendors,
  allSystems,
  enabledVendorIds,
  enabledSystemIds,
  onChange,
  gvl,
}: {
  allVendors: PrivacyExperience["tcf_vendors"];
  allSystems: PrivacyExperience["tcf_systems"];
  enabledVendorIds: string[];
  enabledSystemIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
  gvl?: GVLJson;
}) => {
  const [isFiltered, setIsFiltered] = useState(false);

  // Vendors and Systems are the same for the FE, but are 2 separate
  // objects in the backend. We combine them here but keep them separate
  // when patching preferences
  const vendors = [...(allVendors || []), ...(allSystems || [])];
  const enabledIds = [...enabledVendorIds, ...enabledSystemIds];

  if (vendors.length === 0) {
    // TODO: empty state?
    return null;
  }

  const handleToggle = (vendor: TCFVendorRecord) => {
    const modelType = vendor.has_vendor_id ? "vendors" : "systems";
    if (enabledIds.indexOf(vendor.id) !== -1) {
      onChange({
        newEnabledIds: enabledIds.filter((e) => e !== vendor.id),
        modelType,
      });
    } else {
      onChange({
        newEnabledIds: [...enabledIds, vendor.id],
        modelType,
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
    ? vendors.filter((v) => vendorIsGvl(v, gvl))
    : vendors;

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
          badge={vendorIsGvl(vendor, gvl) ? "GVL" : undefined}
        >
          <div>
            <p>{vendor.description}</p>
            <PurposeVendorDetails
              purposes={vendor.purposes}
              specialPurposes={vendor.special_purposes}
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
