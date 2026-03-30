import { Button, Col, Flex, Row } from "fidesui";
import { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import SystemCard from "~/features/system-inventory/components/SystemCard";
import SystemInventoryFilters from "~/features/system-inventory/components/SystemInventoryFilters";
import SystemStatsRow from "~/features/system-inventory/components/SystemStatsRow";
import { useSystemInventory } from "~/features/system-inventory/hooks/useSystemInventory";

const SystemInventoryPage: NextPage = () => {
  const {
    systems,
    stats,
    search,
    setSearch,
    healthFilter,
    setHealthFilter,
    typeFilter,
    setTypeFilter,
    groupFilter,
    setGroupFilter,
    purposeFilter,
    setPurposeFilter,
    typeOptions,
    groupOptions,
    purposeOptions,
  } = useSystemInventory();

  return (
    <FixedLayout title="Systems">
      <PageHeader
        heading="Systems"
        rightContent={
          <Flex gap="small">
            <Button type="default">Export CSV</Button>
            <Button type="primary">+ Add system</Button>
          </Flex>
        }
      />
      <SystemStatsRow stats={stats} />
      <SystemInventoryFilters
        search={search}
        onSearchChange={setSearch}
        healthFilter={healthFilter}
        onHealthFilterChange={setHealthFilter}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
        groupFilter={groupFilter}
        onGroupFilterChange={setGroupFilter}
        purposeFilter={purposeFilter}
        onPurposeFilterChange={setPurposeFilter}
        typeOptions={typeOptions}
        groupOptions={groupOptions}
        purposeOptions={purposeOptions}
      />
      <Row gutter={[16, 16]}>
        {systems.map((system) => (
          <Col key={system.fides_key} span={8}>
            <SystemCard system={system} />
          </Col>
        ))}
      </Row>
    </FixedLayout>
  );
};

export default SystemInventoryPage;
