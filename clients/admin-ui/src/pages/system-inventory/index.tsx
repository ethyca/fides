import {
  Button,
  Col,
  Divider,
  Flex,
  Icons,
  Row,
  Text,
  Typography,
} from "fidesui";
import { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import GovernanceHealthDashboard from "~/features/system-inventory/components/GovernanceHealthDashboard";
import SystemCard from "~/features/system-inventory/components/SystemCard";
import SystemInventoryFilters from "~/features/system-inventory/components/SystemInventoryFilters";
import { useSystemInventory } from "~/features/system-inventory/hooks/useSystemInventory";

const { Title } = Typography;

const SystemInventoryPage: NextPage = () => {
  const {
    systems,
    needsAttention,
    healthy,
    governanceHealth,
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
    <FixedLayout title="System inventory">
      <PageHeader
        heading="System inventory"
        rightContent={
          <Flex gap="small">
            <Button type="default">Export CSV</Button>
            <Button type="primary">+ Add system</Button>
          </Flex>
        }
      />
      <GovernanceHealthDashboard data={governanceHealth} />
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
      {needsAttention.length > 0 && (
        <div>
          <Flex gap="medium" align="center">
            <Icons.WarningAlt size={20} />
            <div>
              <Title level={4} className="!m-0">
                Needs attention
              </Title>
              <Text type="secondary">
                {needsAttention.length} system
                {needsAttention.length !== 1 ? "s" : ""} with violations or
                governance issues
              </Text>
            </div>
          </Flex>
          <Divider className="mb-4" />
          <Row gutter={[16, 16]}>
            {needsAttention.map((system) => (
              <Col key={system.fides_key} span={8}>
                <SystemCard system={system} />
              </Col>
            ))}
          </Row>
        </div>
      )}
      {healthy.length > 0 && (
        <div className={needsAttention.length > 0 ? "mt-8" : undefined}>
          <Flex gap="medium" align="center">
            <Icons.Checkmark size={20} />
            <div>
              <Title level={4} className="!m-0">
                Healthy
              </Title>
              <Text type="secondary">
                {healthy.length} system{healthy.length !== 1 ? "s" : ""} with no
                issues detected
              </Text>
            </div>
          </Flex>
          <Divider className="mb-4" />
          <Row gutter={[16, 16]}>
            {healthy.map((system) => (
              <Col key={system.fides_key} span={8}>
                <SystemCard system={system} />
              </Col>
            ))}
          </Row>
        </div>
      )}
    </FixedLayout>
  );
};

export default SystemInventoryPage;
