import { Typography } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import RequestLogChart from "./RequestLogChart";
import RequestLogFilters from "./RequestLogFilters";
import RequestLogTable from "./RequestLogTable";
import { RequestLogEntry } from "./types";
import ViolationDetailsDrawer from "./ViolationDetailsDrawer";

const { Title } = Typography;

const RequestLogTab = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [policyFilter, setPolicyFilter] = useState<string | undefined>(
    undefined,
  );
  const [dataUseFilter, setDataUseFilter] = useState<string | undefined>(
    undefined,
  );
  const [timeRange, setTimeRange] = useState("30d");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedViolation, setSelectedViolation] =
    useState<RequestLogEntry | null>(null);

  useEffect(() => {
    if (router.query.policy && typeof router.query.policy === "string") {
      setPolicyFilter(router.query.policy);
    }
  }, [router.query.policy]);

  const handleRowClick = (record: RequestLogEntry) => {
    setSelectedViolation(record);
    setDrawerOpen(true);
  };

  const handleDrawerClose = () => {
    setDrawerOpen(false);
    setSelectedViolation(null);
  };

  return (
    <div>
      <RequestLogFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        policyFilter={policyFilter}
        onPolicyChange={setPolicyFilter}
        dataUseFilter={dataUseFilter}
        onDataUseChange={setDataUseFilter}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
      />
      <RequestLogChart />
      <Title level={5} className="!mb-4">
        Violations
      </Title>
      <RequestLogTable
        policyFilter={policyFilter}
        dataUseFilter={dataUseFilter}
        searchQuery={searchQuery}
        onRowClick={handleRowClick}
      />
      <ViolationDetailsDrawer
        open={drawerOpen}
        onClose={handleDrawerClose}
        violation={selectedViolation}
      />
    </div>
  );
};

export default RequestLogTab;
