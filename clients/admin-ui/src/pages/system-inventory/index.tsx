import {
  Button,
  Col,
  Divider,
  Dropdown,
  Flex,
  Icons,
  Row,
  Text,
  Tooltip,
  Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import GovernanceHealthDashboard from "~/features/system-inventory/components/GovernanceHealthDashboard";
import NeedsAttentionFrame from "~/features/system-inventory/components/NeedsAttentionFrame";
import SystemCard from "~/features/system-inventory/components/SystemCard";
import SystemInventoryFilters from "~/features/system-inventory/components/SystemInventoryFilters";
import { useSystemInventory } from "~/features/system-inventory/hooks/useSystemInventory";

const { Title } = Typography;

const SystemInventoryPage: NextPage = () => {
  const {
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
    severityFilter,
    setSeverityFilter,
    freshnessFilter,
    setFreshnessFilter,
    typeOptions,
    groupOptions,
  } = useSystemInventory();

  const router = useRouter();
  const [cardsExpanded, setCardsExpanded] = useState(false);

  const addSystemsMenu = {
    items: [
      { key: "single", label: "Add system" },
      { key: "multiple", label: "Add multiple systems" },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === "single") {
        router.push(ADD_SYSTEMS_MANUAL_ROUTE);
      } else {
        router.push(ADD_SYSTEMS_MULTIPLE_ROUTE);
      }
    },
  };

  const needsAttentionDescription = `${needsAttention.length} system${
    needsAttention.length !== 1 ? "s" : ""
  } with open risks`;

  const expandToggle = (
    <Tooltip
      title={cardsExpanded ? "Collapse risk details" : "Expand risk details"}
    >
      <Button
        type={cardsExpanded ? "primary" : "default"}
        size="middle"
        aria-label={
          cardsExpanded ? "Collapse risk details" : "Expand risk details"
        }
        icon={<Icons.WarningAlt size={16} />}
        style={
          cardsExpanded
            ? {
                backgroundColor: palette.FIDESUI_MINOS,
                borderColor: palette.FIDESUI_MINOS,
              }
            : undefined
        }
        onClick={() => setCardsExpanded((prev) => !prev)}
      />
    </Tooltip>
  );

  return (
    <FixedLayout title="System inventory">
      <PageHeader
        heading="System inventory"
        rightContent={
          <Dropdown menu={addSystemsMenu} trigger={["click"]}>
            <Button type="primary">
              + Add systems <Icons.ChevronDown size={12} />
            </Button>
          </Dropdown>
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
        severityFilter={severityFilter}
        onSeverityFilterChange={setSeverityFilter}
        freshnessFilter={freshnessFilter}
        onFreshnessFilterChange={setFreshnessFilter}
        typeOptions={typeOptions}
        groupOptions={groupOptions}
        expandToggle={expandToggle}
      />
      {needsAttention.length > 0 && (
        <NeedsAttentionFrame description={needsAttentionDescription}>
          <Row gutter={[16, 16]}>
            {needsAttention.map((system) => (
              <Col key={system.fides_key} span={8}>
                <SystemCard
                  system={system}
                  accentBorder
                  expanded={cardsExpanded}
                />
              </Col>
            ))}
          </Row>
        </NeedsAttentionFrame>
      )}
      {healthy.length > 0 && (
        <div className={needsAttention.length > 0 ? "mt-8" : undefined}>
          <Flex gap="middle" align="center">
            <Icons.Checkmark size={20} />
            <div>
              <Title level={4} className="!m-0">
                Healthy
              </Title>
              <Text type="secondary">
                {healthy.length} system{healthy.length !== 1 ? "s" : ""} with no
                risks detected
              </Text>
            </div>
          </Flex>
          <Divider className="mb-4" />
          <Row gutter={[16, 16]}>
            {healthy.map((system) => (
              <Col key={system.fides_key} span={8}>
                <SystemCard system={system} expanded={cardsExpanded} />
              </Col>
            ))}
          </Row>
        </div>
      )}
    </FixedLayout>
  );
};

export default SystemInventoryPage;
