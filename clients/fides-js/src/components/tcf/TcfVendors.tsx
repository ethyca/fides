import { VNode, h } from "preact";
import { useMemo, useState } from "preact/hooks";
import { Vendor } from "@iabtechlabtcf/core";
import {
  GvlDataCategories,
  GvlDataDeclarations,
  VendorRecord,
  EmbeddedPurpose,
} from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import FilterButtons from "./FilterButtons";
import {
  transformExperienceToVendorRecords,
  vendorGvlEntry,
} from "../../lib/tcf/vendors";
import ExternalLink from "../ExternalLink";
import DoubleToggleTable from "./DoubleToggleTable";

const FILTERS = [{ name: "All vendors" }, { name: "IAB TCF vendors" }];

const VendorDetails = ({
  label,
  lineItems,
}: {
  label: string;
  lineItems: EmbeddedPurpose[] | undefined;
}) => {
  if (!lineItems || lineItems.length === 0) {
    return null;
  }

  const hasRetentionInfo = lineItems.some((li) => li.retention_period != null);

  return (
    <table className="fides-vendor-details-table">
      <thead>
        <tr>
          <th width="80%">{label}</th>
          {hasRetentionInfo ? (
            <th width="20%" style={{ textAlign: "right" }}>
              Retention
            </th>
          ) : null}
        </tr>
      </thead>
      <tbody>
        {lineItems.map((item) => (
          <tr key={item.id}>
            <td>{item.name}</td>
            {hasRetentionInfo ? (
              <td style={{ textAlign: "right" }}>
                {item.retention_period
                  ? `${item.retention_period} day(s)`
                  : "N/A"}
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const PurposeVendorDetails = ({
  purposes,
  specialPurposes,
}: {
  purposes: EmbeddedPurpose[] | undefined;
  specialPurposes: EmbeddedPurpose[] | undefined;
}) => {
  const emptyPurposes = purposes ? purposes.length === 0 : true;
  const emptySpecialPurposes = specialPurposes
    ? specialPurposes.length === 0
    : true;

  if (emptyPurposes && emptySpecialPurposes) {
    return null;
  }

  return (
    <div>
      <VendorDetails label="Purposes" lineItems={purposes} />
      <VendorDetails label="Special purposes" lineItems={specialPurposes} />
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

const StorageDisclosure = ({ vendor }: { vendor: VendorRecord }) => {
  const {
    name,
    uses_cookies: usesCookies,
    uses_non_cookie_access: usesNonCookieAccess,
    cookie_max_age_seconds: cookieMaxAgeSeconds,
    cookie_refresh: cookieRefresh,
  } = vendor;
  let disclosure = "";
  if (usesCookies) {
    const days = cookieMaxAgeSeconds
      ? Math.ceil(cookieMaxAgeSeconds / 60 / 60 / 24)
      : 0;
    disclosure = `${name} stores cookies with a maximum duration of about ${days} Day(s).`;
    if (cookieRefresh) {
      disclosure = `${disclosure} These cookies may be refreshed.`;
    }
    if (usesNonCookieAccess) {
      disclosure = `${disclosure} This vendor also uses other methods like "local storage" to store and access information on your device.`;
    }
  } else if (usesNonCookieAccess) {
    disclosure = `${name} uses methods like "local storage" to store and access information on your device.`;
  }

  if (disclosure === "") {
    return null;
  }

  return <p>{disclosure}</p>;
};

const TcfVendors = ({
  experience,
  enabledVendorConsentIds,
  enabledVendorLegintIds,
  onChange,
  allOnOffButtons,
}: {
  experience: PrivacyExperience;
  enabledVendorConsentIds: string[];
  enabledVendorLegintIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
  allOnOffButtons: VNode;
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

  const handleFilter = (index: number) => {
    if (index === 0) {
      setIsFiltered(false);
    } else {
      setIsFiltered(true);
    }
  };

  const vendorsToDisplay = isFiltered
    ? vendors.filter((v) => vendorGvlEntry(v.id, experience.gvl))
    : vendors;

  return (
    <div>
      <FilterButtons filters={FILTERS} onChange={handleFilter} />
      {allOnOffButtons}
      <DoubleToggleTable<VendorRecord>
        title="Vendors"
        items={vendorsToDisplay}
        enabledConsentIds={enabledVendorConsentIds}
        enabledLegintIds={enabledVendorLegintIds}
        onToggle={onChange}
        consentModelType="vendorsConsent"
        legintModelType="vendorsLegint"
        renderBadgeLabel={(vendor) =>
          vendorGvlEntry(vendor.id, experience.gvl) ? "IAB TCF" : undefined
        }
        renderToggleChild={(vendor) => {
          const gvlVendor = vendorGvlEntry(vendor.id, experience.gvl);
          const dataCategories: GvlDataCategories | undefined =
            // @ts-ignore the IAB-TCF lib doesn't support GVL v3 types yet
            experience.gvl?.dataCategories;
          const hasUrls =
            vendor.privacy_policy_url ||
            vendor.legitimate_interest_disclosure_url;
          return (
            <div>
              <StorageDisclosure vendor={vendor} />
              {hasUrls ? (
                <div style={{ marginBottom: "1.1em" }}>
                  {vendor.privacy_policy_url ? (
                    <ExternalLink href={vendor.privacy_policy_url}>
                      Privacy policy
                    </ExternalLink>
                  ) : null}
                  {vendor.legitimate_interest_disclosure_url ? (
                    <ExternalLink
                      href={vendor.legitimate_interest_disclosure_url}
                    >
                      Legitimate interest disclosure
                    </ExternalLink>
                  ) : null}
                </div>
              ) : null}
              <PurposeVendorDetails
                purposes={[
                  ...(vendor.purpose_consents || []),
                  ...(vendor.purpose_legitimate_interests || []),
                ]}
                specialPurposes={vendor.special_purposes}
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
