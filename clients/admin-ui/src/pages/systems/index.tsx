import { AntButton as Button, AntDropdown, Box, Icons } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
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
    <FixedLayout title="System inventory">
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
        >
          <div className="absolute right-8 top-8">
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
          </div>
        </PageHeader>
        <SystemsTable />
      </Box>
    </FixedLayout>
  );
};

export default Systems;
