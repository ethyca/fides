import { useFeatures } from "common/features";
import { Select, Typography } from "fidesui";
import React, { useMemo } from "react";

import { Option } from "~/features/common/modals/FilterModal";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import {
  useConsentManagementFilters,
} from "~/features/configure-consent/ConsentManagementFilterModal";
import { ConsentManagementTable } from "~/features/configure-consent/ConsentManagementTable";

const updateOptions = (
  setter: (opts: Option[]) => void,
  allOptions: Option[],
  selectedValues: string[],
) => {
  setter(
    allOptions.map((opt) => ({
      ...opt,
      isChecked: selectedValues.includes(opt.value),
    })),
  );
};

const ConfigureConsentPage = () => {
  const { tcf: isTcfEnabled } = useFeatures();

  const {
    resetFilters,
    purposeOptions,
    setPurposeOptions,
    dataUseOptions,
    setDataUseOptions,
    legalBasisOptions,
    setLegalBasisOptions,
    consentCategoryOptions,
    setConsentCategoryOptions,
  } = useConsentManagementFilters();

  const activeCount = useMemo(
    () =>
      [purposeOptions, dataUseOptions, legalBasisOptions, consentCategoryOptions]
        .flat()
        .filter((o) => o.isChecked).length,
    [purposeOptions, dataUseOptions, legalBasisOptions, consentCategoryOptions],
  );

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Vendors"
          description="Manage your vendors. Modify the legal basis for a vendor if permitted and filter your view."
        />
        <SidePanel.Filters activeCount={activeCount} onClearAll={resetFilters}>
          {isTcfEnabled ? (
            <div>
              <Typography.Text
                type="secondary"
                style={{ fontSize: 12, display: "block", marginBottom: 4 }}
              >
                TCF purposes
              </Typography.Text>
              <Select
                mode="multiple"
                placeholder="All purposes"
                style={{ width: "100%" }}
                value={purposeOptions
                  .filter((o) => o.isChecked)
                  .map((o) => o.value)}
                onChange={(values: string[]) =>
                  updateOptions(setPurposeOptions, purposeOptions, values)
                }
                options={purposeOptions.map((o) => ({
                  value: o.value,
                  label: o.displayText,
                }))}
              />
            </div>
          ) : null}
          <div>
            <Typography.Text
              type="secondary"
              style={{ fontSize: 12, display: "block", marginBottom: 4 }}
            >
              Data uses
            </Typography.Text>
            <Select
              mode="multiple"
              placeholder="All data uses"
              style={{ width: "100%" }}
              value={dataUseOptions
                .filter((o) => o.isChecked)
                .map((o) => o.value)}
              onChange={(values: string[]) =>
                updateOptions(setDataUseOptions, dataUseOptions, values)
              }
              options={dataUseOptions.map((o) => ({
                value: o.value,
                label: o.displayText,
              }))}
            />
          </div>
          {isTcfEnabled ? (
            <div>
              <Typography.Text
                type="secondary"
                style={{ fontSize: 12, display: "block", marginBottom: 4 }}
              >
                Legal basis
              </Typography.Text>
              <Select
                mode="multiple"
                placeholder="All legal bases"
                style={{ width: "100%" }}
                value={legalBasisOptions
                  .filter((o) => o.isChecked)
                  .map((o) => o.value)}
                onChange={(values: string[]) =>
                  updateOptions(
                    setLegalBasisOptions,
                    legalBasisOptions,
                    values,
                  )
                }
                options={legalBasisOptions.map((o) => ({
                  value: o.value,
                  label: o.displayText,
                }))}
              />
            </div>
          ) : null}
          {!isTcfEnabled ? (
            <div>
              <Typography.Text
                type="secondary"
                style={{ fontSize: 12, display: "block", marginBottom: 4 }}
              >
                Consent categories
              </Typography.Text>
              <Select
                mode="multiple"
                placeholder="All categories"
                style={{ width: "100%" }}
                value={consentCategoryOptions
                  .filter((o) => o.isChecked)
                  .map((o) => o.value)}
                onChange={(values: string[]) =>
                  updateOptions(
                    setConsentCategoryOptions,
                    consentCategoryOptions,
                    values,
                  )
                }
                options={consentCategoryOptions.map((o) => ({
                  value: o.value,
                  label: o.displayText,
                }))}
              />
            </div>
          ) : null}
        </SidePanel.Filters>
      </SidePanel>
      <Layout title="Vendors">
        <ConsentManagementTable
          purposeOptions={purposeOptions}
          dataUseOptions={dataUseOptions}
          legalBasisOptions={legalBasisOptions}
          consentCategoryOptions={consentCategoryOptions}
        />
      </Layout>
    </>
  );
};

export default ConfigureConsentPage;
