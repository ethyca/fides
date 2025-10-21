import { AntButton as Button, AntDropdown, Box, Icons } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SystemsTable from "~/features/system/SystemsTable";

const Systems: NextPage = () => {
  const router = useRouter();
  const { dictionaryService: isCompassEnabled } = useFeatures();

  return (
    <Layout title="System inventory" mainProps={{ w: "calc(100vw - 240px)" }}>
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
          isSticky={false}
          style={{ position: "relative" }}
        >
          {isCompassEnabled && (
            <AntDropdown
              trigger={["click"]}
              menu={{
                items: [
                  {
                    label: "Create new system",
                    key: "add-system",
                    onClick: () => router.push(ADD_SYSTEMS_MANUAL_ROUTE),
                  },
                  {
                    label: "Add multiple systems",
                    key: "add-multiple-systems",
                    onClick: () => router.push(ADD_SYSTEMS_MULTIPLE_ROUTE),
                  },
                ],
              }}
            >
              <Button
                type="primary"
                data-testid="add-system-btn"
                icon={<Icons.ChevronDown />}
                className="absolute right-0 top-0"
              >
                Add system
              </Button>
            </AntDropdown>
          )}
          {!isCompassEnabled && (
            <Button
              type="primary"
              data-testid="add-system-btn"
              onClick={() => router.push(ADD_SYSTEMS_MANUAL_ROUTE)}
            >
              Add new system
            </Button>
          )}
        </PageHeader>
        <SystemsTable />
      </Box>
    </Layout>
  );
};

export default Systems;
