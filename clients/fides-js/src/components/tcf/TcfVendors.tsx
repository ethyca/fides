import { h } from "preact";
import { useState } from "preact/hooks";
import { Vendor } from "@iabtechlabtcf/core";
import {
  EmbeddedLineItem,
  EmbeddedPurpose,
  GVLJson,
  TCFVendorRecord,
  VendorUrl,
} from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";
import FilterButtons from "./FilterButtons";
import { vendorIsGvl } from "../../lib/tcf/vendors";
import LegalBasisDropdown, {
  useLegalBasisDropdown,
} from "./LegalBasisDropdown";
import ExternalLink from "../ExternalLink";

const FILTERS = [{ name: "All vendors" }, { name: "IAB TCF vendors" }];

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

const StorageDisclosure = ({ vendor }: { vendor: Vendor }) => {
  const { name, usesCookies, usesNonCookieAccess, cookieMaxAgeSeconds } =
    vendor;
  let disclosure = "";
  if (usesCookies) {
    const days = cookieMaxAgeSeconds
      ? (cookieMaxAgeSeconds / 60 / 60 / 24).toFixed(2)
      : 0;
    disclosure = `${name} stores cookies with a maximum duration of about ${days} Day(s) (${cookieMaxAgeSeconds} Second(s)).`;
  }
  if (usesNonCookieAccess) {
    disclosure = `${disclosure} This vendor also uses other methods like "local storage" to store and access information on your device.`;
  }

  return <p>{disclosure}</p>;
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
      {vendorsToDisplay.map((vendor) => {
        const gvlVendor = vendorIsGvl(vendor, gvl);
        // @ts-ignore the IAB-TCF lib doesn't support GVL v3 types yet
        const url: VendorUrl = gvlVendor?.urls.find(
          (u: VendorUrl) => u.langId === "en"
        );
        return (
          <DataUseToggle
            dataUse={{ key: vendor.id, name: vendor.name }}
            onToggle={() => {
              handleToggle(vendor);
            }}
            checked={enabledIds.indexOf(vendor.id) !== -1}
            badge={gvlVendor ? "IAB TCF" : undefined}
          >
            <div>
              {gvlVendor ? <StorageDisclosure vendor={gvlVendor} /> : null}
              <div>
                {url?.privacy ? (
                  <ExternalLink href={url.privacy}>Privacy policy</ExternalLink>
                ) : null}
                {url?.legIntClaim ? (
                  <ExternalLink href={url.legIntClaim}>
                    Legitimate interest disclosure
                  </ExternalLink>
                ) : null}
              </div>
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
        );
      })}
    </div>
  );
};

export default TcfVendors;
