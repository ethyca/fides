import { Button, Icons, Tooltip } from "fidesui";
import { useRouter } from "next/router";

import { useMonitorReportDownload } from "./useMonitorReportDownload";

const MonitorReportDownload = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const { isGenerating, generate } = useMonitorReportDownload(monitorId);

  return (
    <Tooltip title="Generate Report">
      <Button
        aria-label="Generate Report"
        icon={<Icons.Document />}
        onClick={() => generate()}
        loading={isGenerating}
        disabled={isGenerating}
      />
    </Tooltip>
  );
};

export default MonitorReportDownload;
