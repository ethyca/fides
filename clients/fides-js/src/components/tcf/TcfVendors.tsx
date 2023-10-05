import { h } from "preact";
import { useMemo, useState } from "preact/hooks";
import { Vendor } from "@iabtechlabtcf/core";
import {
  GvlDataRetention,
  EmbeddedLineItem,
  GvlDataCategories,
  GvlVendorUrl,
  GvlDataDeclarations,
  VendorRecord,
} from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import FilterButtons from "./FilterButtons";
import {
  transformExperienceToVendorRecords,
  vendorIsGvl,
} from "../../lib/tcf/vendors";
import ExternalLink from "../ExternalLink";
import DoubleToggleTable from "./DoubleToggleTable";

const FILTERS = [{ name: "All vendors" }, { name: "IAB TCF vendors" }];

interface Retention {
  mapping: Record<number, number>;
  default: number;
}

const VendorDetails = ({
  label,
  lineItems,
  dataRetention,
}: {
  label: string;
  lineItems: EmbeddedLineItem[] | undefined;
  dataRetention?: Retention;
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
          let retention: string | number = "N/A";
          if (dataRetention) {
            retention = dataRetention.mapping[item.id] ?? dataRetention.default;
          }
          return (
            <tr key={item.id}>
              <td>{item.name}</td>
              {dataRetention ? (
                <td>{retention == null ? "N/A" : `${retention} day(s)`}</td>
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
  purposes: EmbeddedLineItem[] | undefined;
  specialPurposes: EmbeddedLineItem[] | undefined;
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
        dataRetention={
          dataRetention
            ? {
                mapping: dataRetention.purposes,
                default: dataRetention.stdRetention,
              }
            : undefined
        }
      />
      <VendorDetails
        label="Special purposes"
        lineItems={specialPurposes as EmbeddedLineItem[]}
        dataRetention={
          dataRetention
            ? {
                mapping: dataRetention.specialPurposes,
                default: dataRetention.stdRetention,
              }
            : undefined
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
  experience,
  enabledVendorConsentIds,
  enabledVendorLegintIds,
  onChange,
}: {
  experience: PrivacyExperience;
  enabledVendorConsentIds: string[];
  enabledVendorLegintIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => {
  const [isFiltered, setIsFiltered] = useState(false);

  // Combine the various vendor objects into one object for convenience
  const vendors = useMemo(
    () => transformExperienceToVendorRecords(experience),
    [experience]
  );

  if (!vendors || vendors.length === 0) {
    // TODO: empty state?
    return null;
  }

  const handleToggle = (vendor: VendorRecord) => {
    const enabledIds = vendor.isConsent
      ? enabledVendorConsentIds
      : enabledVendorLegintIds;
    const modelType = vendor.isConsent ? "vendorsConsent" : "vendorsLegint";
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
    ? vendors.filter((v) => vendorIsGvl(v, experience.gvl))
    : vendors;

  return (
    <div>
      <FilterButtons filters={FILTERS} onChange={handleFilter} />
      <DoubleToggleTable<VendorRecord>
        items={vendorsToDisplay}
        enabledConsentIds={enabledVendorConsentIds}
        enabledLegintIds={enabledVendorLegintIds}
        onToggle={handleToggle}
        renderBadgeLabel={(vendor) =>
          vendorIsGvl(vendor, experience.gvl) ? "IAB TCF" : undefined
        }
        renderToggleChild={(vendor) => {
          const gvlVendor = vendorIsGvl(vendor, experience.gvl);
          // @ts-ignore the IAB-TCF lib doesn't support GVL v3 types yet
          const url: GvlVendorUrl | undefined = gvlVendor?.urls.find(
            (u: GvlVendorUrl) => u.langId === "en"
          );
          const dataCategories: GvlDataCategories | undefined =
            // @ts-ignore the IAB-TCF lib doesn't support GVL v3 types yet
            experience.gvl?.dataCategories;
          return (
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
                purposes={[
                  ...(vendor.consent_purposes || []),
                  ...(vendor.legitimate_interests_purposes || []),
                ]}
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
          );
        }}
      />
    </div>
  );
};

export default TcfVendors;
