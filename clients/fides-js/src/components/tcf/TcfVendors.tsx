import { h } from "preact";
import { useState } from "preact/hooks";
import { Vendor } from "@iabtechlabtcf/core";
import {
  GvlDataRetention,
  EmbeddedLineItem,
  EmbeddedPurpose,
  GVLJson,
  GvlDataCategories,
  TCFVendorRecord,
  GvlVendorUrl,
  GvlDataDeclarations,
} from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";
import FilterButtons from "./FilterButtons";
import { vendorIsGvl } from "../../lib/tcf/vendors";
import ExternalLink from "../ExternalLink";

const FILTERS = [{ name: "All vendors" }, { name: "IAB TCF vendors" }];

const VendorDetails = ({
  label,
  lineItems,
  dataRetention,
}: {
  label: string;
  lineItems: EmbeddedLineItem[] | undefined;
  dataRetention?: Record<number, number>;
}) => {
  if (!lineItems || lineItems.length === 0) {
    return null;
  }

  return (
    <table className="fides-vendor-details-table">
      <thead>
        <tr>
          <th>{label}</th>
          {dataRetention ? <th>Retention</th> : null}
        </tr>
      </thead>
      <tbody>
        {lineItems.map((item) => {
          const retention = dataRetention ? dataRetention[item.id] : undefined;
          return (
            <tr key={item.id}>
              <td>{item.name}</td>
              {dataRetention ? (
                <td>{retention == null ? "N/A" : retention}</td>
              ) : null}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

const PurposeVendorDetails = ({
  purposes,
  specialPurposes,
  gvlVendor,
}: {
  purposes: EmbeddedPurpose[] | undefined;
  specialPurposes: EmbeddedPurpose[] | undefined;
  gvlVendor: Vendor | undefined;
}) => {
  const emptyPurposes = purposes ? purposes.length === 0 : true;
  const emptySpecialPurposes = specialPurposes
    ? specialPurposes.length === 0
    : true;

  if (emptyPurposes && emptySpecialPurposes) {
    return null;
  }
  // @ts-ignore our TCF lib does not have GVL v3 types yet
  const dataRetention: GvlDataRetention | undefined = gvlVendor?.dataRetention;

  return (
    <div>
      <VendorDetails
        label="Purposes"
        lineItems={purposes as EmbeddedLineItem[]}
        dataRetention={dataRetention ? dataRetention.purposes : undefined}
      />
      <VendorDetails
        label="Special purposes"
        lineItems={specialPurposes as EmbeddedLineItem[]}
        dataRetention={
          dataRetention ? dataRetention.specialPurposes : undefined
        }
      />
    </div>
  );
};

const DataCategories = ({
  gvlVendor,
  dataCategories,
}: {
  gvlVendor: Vendor | undefined;
  dataCategories: GvlDataCategories | undefined;
}) => {
  if (!gvlVendor || !dataCategories) {
    return null;
  }

  // @ts-ignore this type doesn't exist in v2.2 but does in v3
  const declarations: GvlDataDeclarations = gvlVendor.dataDeclaration;

  return (
    <table className="fides-vendor-details-table">
      <thead>
        <tr>
          <th>Data categories</th>
        </tr>
      </thead>
      <tbody>
        {declarations.map((id) => {
          const category = dataCategories[id];
          return (
            <tr key={id}>
              <td>{category.name}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

const StorageDisclosure = ({ vendor }: { vendor: Vendor }) => {
  const {
    name,
    usesCookies,
    usesNonCookieAccess,
    cookieMaxAgeSeconds,
    cookieRefresh,
  } = vendor;
  let disclosure = "";
  if (usesCookies) {
    const days = cookieMaxAgeSeconds
      ? Math.ceil(cookieMaxAgeSeconds / 60 / 60 / 24)
      : 0;
    disclosure = `${name} stores cookies with a maximum duration of about ${days} Day(s).`;
  }
  if (cookieRefresh) {
    disclosure = `${disclosure} These cookies may be refreshed.`;
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
        const url: GvlVendorUrl | undefined = gvlVendor?.urls.find(
          (u: GvlVendorUrl) => u.langId === "en"
        );
        const dataCategories: GvlDataCategories | undefined =
          // @ts-ignore the IAB-TCF lib doesn't support GVL v3 types yet
          gvl?.dataCategories;
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
                gvlVendor={gvlVendor}
              />

              <VendorDetails label="Features" lineItems={vendor.features} />
              <VendorDetails
                label="Special features"
                lineItems={vendor.special_features}
              />
              <DataCategories
                gvlVendor={gvlVendor}
                dataCategories={dataCategories}
              />
            </div>
          </DataUseToggle>
        );
      })}
    </div>
  );
};

export default TcfVendors;
