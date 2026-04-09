import { Flex } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRef } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";

import CdnRequestsChart from "~/features/bending-spoons/components/CdnRequestsChart";
import ExportButton from "~/features/bending-spoons/components/ExportButton";
import HeadlinesCard from "~/features/bending-spoons/components/HeadlinesCard";

const BendingSpoonsPage: NextPage = () => {
  const chartRef = useRef<HTMLDivElement>(null);
  const headlinesRef = useRef<HTMLDivElement>(null);

  return (
    <FixedLayout title="Bending Spoons">
      <PageHeader heading="Bending Spoons" />
      <Flex vertical align="center" gap={40}>
        <div>
          <Flex justify="flex-end" className="mb-2">
            <ExportButton targetRef={chartRef} filename="cdn-requests-chart" />
          </Flex>
          <div
            style={{
              backgroundColor: palette.FIDESUI_MINOS,
              borderRadius: 10,
              padding: 8,
            }}
          >
            <CdnRequestsChart ref={chartRef} />
          </div>
        </div>

        <div>
          <Flex justify="flex-end" className="mb-2">
            <ExportButton
              targetRef={headlinesRef}
              filename="headlines-kpi"
            />
          </Flex>
          <HeadlinesCard ref={headlinesRef} />
        </div>
      </Flex>
    </FixedLayout>
  );
};

export default BendingSpoonsPage;
