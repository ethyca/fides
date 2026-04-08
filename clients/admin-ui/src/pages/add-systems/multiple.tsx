import { useFeatures } from "common/features";
import {
  ChakraBox as Box,
  ChakraText as Text,
  Link as LinkText,
  Select,
  Typography,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useCallback, useMemo, useState } from "react";

import { vendorSourceLabels, VendorSources } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_ROUTE,
  DATAMAP_ROUTE,
} from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { AddMultipleSystems } from "~/features/system/add-multiple-systems/AddMultipleSystems";

const DESCRIBE_SYSTEM_COPY =
  "Select your vendors below and they will be added as systems to your data map. Fides Compass will automatically populate the system information so that you can quickly configure privacy requests and consent. Add custom systems or unlisted vendors on the ";

const sourceOptions = [
  {
    value: VendorSources.GVL,
    label: vendorSourceLabels[VendorSources.GVL].fullName,
  },
  {
    value: VendorSources.AC,
    label: vendorSourceLabels[VendorSources.AC].fullName,
  },
];

const AddMultipleSystemsPage: NextPage = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  const activeCount = useMemo(
    () => selectedSources.length,
    [selectedSources],
  );

  const resetFilters = useCallback(() => {
    setSelectedSources([]);
  }, []);

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Add systems"
          breadcrumbItems={[
            {
              title: "Add systems",
              href: ADD_SYSTEMS_ROUTE,
            },
            { title: "Choose vendors" },
          ]}
        />
        {isTcfEnabled ? (
          <SidePanel.Filters
            activeCount={activeCount}
            onClearAll={resetFilters}
          >
            <div>
              <Typography.Text
                type="secondary"
                style={{ fontSize: 12, display: "block", marginBottom: 4 }}
              >
                Sources
              </Typography.Text>
              <Select
                mode="multiple"
                placeholder="All sources"
                style={{ width: "100%" }}
                value={selectedSources}
                onChange={setSelectedSources}
                options={sourceOptions}
              />
            </div>
          </SidePanel.Filters>
        ) : null}
      </SidePanel>
      <Layout title="Choose vendors">
        <Box w={{ base: "100%", md: "75%" }}>
          <Text fontSize="sm" mb={8}>
            {DESCRIBE_SYSTEM_COPY}
            <NextLink href={ADD_SYSTEMS_MANUAL_ROUTE} passHref legacyBehavior>
              <LinkText>Add a system</LinkText>
            </NextLink>{" "}
            page.
          </Text>
        </Box>
        <AddMultipleSystems
          redirectRoute={DATAMAP_ROUTE}
          selectedSources={selectedSources}
        />
      </Layout>
    </>
  );
};

export default AddMultipleSystemsPage;
