import { Fragment, h } from "preact";
import { useMemo, useState } from "preact/hooks";
import { Vendor } from "@iabtechlabtcf/core";
import { PrivacyExperience } from "../../lib/consent-types";
import { I18n } from "../../lib/i18n";
import { LEGAL_BASIS_OPTIONS } from "../../lib/tcf/constants";
import {
  GvlDataCategories,
  GvlDataDeclarations,
  VendorRecord,
  EmbeddedPurpose,
  LegalBasisEnum,
} from "../../lib/tcf/types";
import {
  transformExperienceToVendorRecords,
  vendorGvlEntry,
} from "../../lib/tcf/vendors";
import { UpdateEnabledIds } from "./TcfOverlay";
import ExternalLink from "../ExternalLink";
import RecordsList from "./RecordsList";
import RadioGroup from "./RadioGroup";
import PagingButtons, { usePaging } from "../PagingButtons";

type VendorDetailsType =
  | "purposes"
  | "specialPurposes"
  | "features"
  | "specialFeatures";

const VendorDetails = ({
  i18n,
  type,
  label,
  lineItems,
}: {
  i18n: I18n;
  type: VendorDetailsType;
  label: string;
  lineItems: EmbeddedPurpose[] | undefined;
}) => {
  if (!lineItems || lineItems.length === 0) {
    return null;
  }

  const hasRetentionInfo = lineItems.some((li) => li.retention_period != null);

  // TODO (PROD-1683): update i18n for retention periods based on translator feedback
  return (
    <table className="fides-vendor-details-table">
      <thead>
        <tr>
          <th width="80%">{label}</th>
          {hasRetentionInfo ? (
            <th width="20%" style={{ textAlign: "right" }}>
              {i18n.t("static.tcf.retention")}
            </th>
          ) : null}
        </tr>
      </thead>
      <tbody>
        {lineItems.map((item) => (
          <tr key={item.id}>
            <td>{i18n.t(`exp.tcf.${type}.${item.id}.name`)}</td>
            {hasRetentionInfo ? (
              <td style={{ textAlign: "right" }}>
                {
                  item.retention_period
                    ? `${item.retention_period} ${i18n.t(
                        "static.tcf.retention_period_days"
                      )}`
                    : "-" /* show "-" instead of "N/A" to be language-agnostic */
                }
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const PurposeVendorDetails = ({
  i18n,
  purposes,
  specialPurposes,
}: {
  i18n: I18n;
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
    <Fragment>
      <VendorDetails
        i18n={i18n}
        type="purposes"
        label={i18n.t("static.tcf.purposes")}
        lineItems={purposes}
      />
      <VendorDetails
        i18n={i18n}
        type="specialPurposes"
        label={i18n.t("static.tcf.special_purposes")}
        lineItems={specialPurposes}
      />
    </Fragment>
  );
};

const DataCategories = ({
  i18n,
  gvlVendor,
  dataCategories,
}: {
  i18n: I18n;
  gvlVendor: Vendor | undefined;
  dataCategories: GvlDataCategories | undefined;
}) => {
  if (!gvlVendor || !dataCategories) {
    return null;
  }

  const declarations: GvlDataDeclarations | undefined =
    // @ts-ignore this type doesn't exist in v2.2 but does in v3
    gvlVendor.dataDeclaration;

  return (
    <table className="fides-vendor-details-table">
      <thead>
        <tr>
          <th>{i18n.t("static.tcf.data_categories")}</th>
        </tr>
      </thead>
      <tbody>
        {declarations?.map((id) => (
          <tr key={id}>
            <td>{i18n.t(`exp.tcf.dataCategories.${id}.name`)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const StorageDisclosure = ({
  i18n,
  vendor,
}: {
  i18n: I18n;
  vendor: VendorRecord;
}) => {
  const {
    name,
    uses_cookies: usesCookies,
    uses_non_cookie_access: usesNonCookieAccess,
    cookie_max_age_seconds: cookieMaxAgeSeconds,
    cookie_refresh: cookieRefresh,
  } = vendor;
  // TODO (PROD-1683): better i18n solution for storage disclosure
  /* eslint-disable prefer-template */
  let disclosure = "";
  if (usesCookies) {
    const days = cookieMaxAgeSeconds
      ? Math.ceil(cookieMaxAgeSeconds / 60 / 60 / 24)
      : 0;
    const disclosureIntro = `${name} ${i18n.t(
      "static.tcf.cookie_disclosure.intro"
    )} ${days} ${i18n.t("static.tcf.retention_period_days")}.`;
    disclosure += disclosureIntro;
    if (cookieRefresh) {
      disclosure += " " + i18n.t("static.tcf.cookie_disclosure.refresh");
    }
    if (usesNonCookieAccess) {
      disclosure +=
        " " + i18n.t("static.tcf.cookie_disclosure.also_non_cookie");
    }
  } else if (usesNonCookieAccess) {
    disclosure += " " + i18n.t("static.tcf.cookie_disclosure.non_cookie");
  }
  /* eslint-enable prefer-template */

  if (disclosure === "") {
    return null;
  }

  // Return null if the disclosure string is empty
  if (!disclosure) {
    return null;
  }

  return <p>{disclosure}</p>;
};

const ToggleChild = ({
  vendor,
  experience,
  i18n,
}: {
  vendor: VendorRecord;
  experience: PrivacyExperience;
  i18n: I18n;
}) => {
  const gvlVendor = vendorGvlEntry(vendor.id, experience.gvl);
  const dataCategories: GvlDataCategories | undefined =
    // @ts-ignore the IAB-TCF lib doesn't support GVL v3 types yet
    experience.gvl?.dataCategories;
  // DEFER (PROD-1804): Check to see if localized URLs exist in the GVL vendor data
  const hasUrls =
    vendor.privacy_policy_url || vendor.legitimate_interest_disclosure_url;
  return (
    <Fragment>
      <StorageDisclosure i18n={i18n} vendor={vendor} />
      {hasUrls && (
        <div>
          {vendor.privacy_policy_url && (
            <ExternalLink href={vendor.privacy_policy_url}>
              {i18n.t("static.tcf.privacy_policy")}
            </ExternalLink>
          )}
          {vendor.legitimate_interest_disclosure_url && (
            <ExternalLink href={vendor.legitimate_interest_disclosure_url}>
              {i18n.t("static.tcf.legint_disclosure")}
            </ExternalLink>
          )}
        </div>
      )}
      <PurposeVendorDetails
        i18n={i18n}
        purposes={[
          ...(vendor.purpose_consents || []),
          ...(vendor.purpose_legitimate_interests || []),
        ]}
        specialPurposes={vendor.special_purposes}
      />
      <VendorDetails
        i18n={i18n}
        type="features"
        label={i18n.t("static.tcf.features")}
        lineItems={vendor.features}
      />
      <VendorDetails
        i18n={i18n}
        type="specialFeatures"
        label={i18n.t("static.tcf.special_features")}
        lineItems={vendor.special_features}
      />
      <DataCategories
        i18n={i18n}
        gvlVendor={gvlVendor}
        dataCategories={dataCategories}
      />
    </Fragment>
  );
};

const PagedVendorData = ({
  i18n,
  experience,
  vendors,
  enabledIds,
  onChange,
}: {
  i18n: I18n;
  experience: PrivacyExperience;
  vendors: VendorRecord[];
  enabledIds: string[];
  onChange: (newIds: string[]) => void;
}) => {
  const { activeChunk, totalPages, ...paging } = usePaging(vendors);

  const {
    gvlVendors,
    otherVendors,
  }: {
    gvlVendors: VendorRecord[];
    otherVendors: VendorRecord[];
  } = useMemo(
    () => ({
      gvlVendors: activeChunk.filter((v) => v.isGvl),
      otherVendors: activeChunk.filter((v) => !v.isGvl),
    }),
    [activeChunk]
  );

  return (
    <Fragment>
      <RecordsList<VendorRecord>
        i18n={i18n}
        type="vendors"
        title={i18n.t("static.tcf.vendors.iab")}
        items={gvlVendors}
        enabledIds={enabledIds}
        onToggle={onChange}
        renderBadgeLabel={(vendor) =>
          vendorGvlEntry(vendor.id, experience.gvl)
            ? i18n.t("static.tcf.iab")
            : undefined
        }
        renderToggleChild={(vendor) => (
          <ToggleChild i18n={i18n} vendor={vendor} experience={experience} />
        )}
      />
      <RecordsList<VendorRecord>
        i18n={i18n}
        type="vendors"
        title={i18n.t("static.tcf.vendors.other")}
        items={otherVendors}
        enabledIds={enabledIds}
        onToggle={onChange}
        renderToggleChild={(vendor) => (
          <ToggleChild i18n={i18n} vendor={vendor} experience={experience} />
        )}
      />
      <PagingButtons {...paging} />
    </Fragment>
  );
};

const TcfVendors = ({
  i18n,
  experience,
  enabledVendorConsentIds,
  enabledVendorLegintIds,
  onChange,
}: {
  i18n: I18n;
  experience: PrivacyExperience;
  enabledVendorConsentIds: string[];
  enabledVendorLegintIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => {
  // Combine the various vendor objects into one object for convenience
  const vendors = useMemo(
    () => transformExperienceToVendorRecords(experience),
    [experience]
  );

  const [activeLegalBasisOption, setActiveLegalBasisOption] = useState(
    LEGAL_BASIS_OPTIONS[0]
  );

  const filteredVendors = useMemo(() => {
    const legalBasisFiltered =
      activeLegalBasisOption.value === LegalBasisEnum.CONSENT.toString()
        ? vendors.filter((v) => v.isConsent)
        : vendors.filter((v) => v.isLegint);
    // Put "other vendors" last in the list
    return [
      ...legalBasisFiltered.filter((v) => v.isGvl),
      ...legalBasisFiltered.filter((v) => !v.isGvl),
    ];
  }, [activeLegalBasisOption, vendors]);

  return (
    <div>
      <RadioGroup
        i18n={i18n}
        options={LEGAL_BASIS_OPTIONS}
        active={activeLegalBasisOption}
        onChange={setActiveLegalBasisOption}
      />
      <PagedVendorData
        i18n={i18n}
        experience={experience}
        vendors={filteredVendors}
        enabledIds={
          activeLegalBasisOption.value === LegalBasisEnum.CONSENT.toString()
            ? enabledVendorConsentIds
            : enabledVendorLegintIds
        }
        onChange={(newEnabledIds) =>
          onChange({
            newEnabledIds,
            modelType:
              activeLegalBasisOption.value === LegalBasisEnum.CONSENT.toString()
                ? "vendorsConsent"
                : "vendorsLegint",
          })
        }
        // This key forces a rerender when legal basis changes, which allows paging to reset properly
        key={`vendor-data-${activeLegalBasisOption.value}`}
      />
    </div>
  );
};

export default TcfVendors;
