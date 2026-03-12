import { Flex, Select, Typography } from "fidesui";
import { useState } from "react";

import DataConsumersCard from "./DataConsumersCard";
import FindingsTable from "./FindingsTable";
import { TIME_RANGE_OPTIONS } from "./mock-data";
import ViolationRateCard from "./ViolationRateCard";
import ViolationsOverTimeCard from "./ViolationsOverTimeCard";

const { Title } = Typography;

const SummaryTab = () => {
  const [timeRange, setTimeRange] = useState("30d");

  return (
    <div>
      <Flex justify="flex-end" className="mb-6">
        <Select
          aria-label="Time range"
          value={timeRange}
          onChange={setTimeRange}
          options={TIME_RANGE_OPTIONS}
          className="w-48"
        />
      </Flex>

      <div className="mb-10 grid grid-cols-3 gap-4">
        <ViolationsOverTimeCard />
        <ViolationRateCard />
        <DataConsumersCard />
      </div>

      <div>
        <Title level={5} className="!mb-4">
          Findings
        </Title>
        <FindingsTable />
      </div>
    </div>
  );
};

export default SummaryTab;
