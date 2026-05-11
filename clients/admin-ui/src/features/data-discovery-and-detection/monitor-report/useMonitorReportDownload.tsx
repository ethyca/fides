import { pdf } from "@react-pdf/renderer";
import { useMessage } from "fidesui";
import _ from "lodash";
import { useCallback, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { getBrandLogoUrl, getDomain } from "~/features/common/utils";
import {
  useLazyGetAggregateStatisticsQuery,
  useLazyGetClassificationsQuery,
  useLazyGetMonitorConfigQuery,
  useLazyGetVendorsQuery,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { MonitorReport } from "~/features/data-discovery-and-detection/monitor-report/MonitorReport";
import { APIMonitorType } from "~/types/api";

import MonitorReportClassificationsChart from "./charts/MonitorReportClassificationsChart";
import MonitorReportVendorsChart from "./charts/MonitorReportVendorsChart";
import {
  downloadBlob,
  generateChart,
  getImageBlob,
  getRootClassifications,
} from "./utils";

export const useMonitorReportDownload = (monitorId: string) => {
  const currentUser = useAppSelector(selectUser);
  const messageApi = useMessage();
  const [isGenerating, setIsGenerating] = useState<boolean>();
  const [isLoading, setIsLoading] = useState<boolean>();

  const [vendorsTrigger] = useLazyGetVendorsQuery();
  const [classificationsTrigger] = useLazyGetClassificationsQuery();
  const [statsTrigger] = useLazyGetAggregateStatisticsQuery();
  const [configTrigger] = useLazyGetMonitorConfigQuery();

  const generate = useCallback(async () => {
    setIsGenerating(true);
    setIsLoading(true);

    const fetchAll = async () =>
      Promise.all([
        vendorsTrigger({ monitor_config_id: monitorId }),
        statsTrigger({
          monitor_type: APIMonitorType.WEBSITE,
          monitor_config_id: monitorId,
        }),
        classificationsTrigger({ monitor_config_id: monitorId }),
        configTrigger({ monitor_config_id: monitorId }),
      ]).then(
        async ([
          { data: vendorsData },
          { data: statsData },
          { data: classificationsData },
          { data: configData },
        ]) => {
          setIsLoading(false);

          if (
            vendorsData?.vendors &&
            statsData &&
            classificationsData?.classifications &&
            configData
          ) {
            const fullName =
              currentUser?.first_name && currentUser.last_name
                ? `${currentUser?.first_name} ${currentUser?.last_name}`
                : null;
            const author =
              fullName ??
              currentUser?.email_address ??
              currentUser?.username ??
              "";

            const vendors = vendorsData.vendors?.toSorted(
              (a, b) => (b.resource_count ?? 0) - (a.resource_count ?? 0),
            );

            const classifications =
              classificationsData.classifications?.toSorted(
                (a, b) => (b.vendors?.length ?? 0) - (a.vendors?.length ?? 0),
              );

            const [vendorChart, classificationsChart, imageSrcResponse] =
              await Promise.all([
                generateChart(
                  <MonitorReportVendorsChart vendors={vendors ?? []} />,
                ),
                generateChart(
                  <MonitorReportClassificationsChart
                    classifications={getRootClassifications(
                      classifications ?? [],
                    )}
                  />,
                ),
                getImageBlob(
                  _(
                    !!configData?.datasource_params &&
                      "sitemap_url" in configData.datasource_params &&
                      typeof configData.datasource_params.sitemap_url ===
                        "string"
                      ? configData.datasource_params.sitemap_url
                      : configData.name,
                  )
                    .thru(getDomain)
                    .thru((domain) => getBrandLogoUrl(domain, 400))
                    .value(),
                ),
              ]);

            if (!vendorChart || !classificationsChart || !imageSrcResponse) {
              setIsGenerating(false);
              messageApi.error("Error generating images for pdf");
              return;
            }

            // Sometimes this just fails silently
            const generatedPdf = pdf(
              <MonitorReport
                stats={statsData}
                classifications={classifications}
                vendors={vendors}
                monitorTitle={configData.name}
                imageSrc={imageSrcResponse}
                vendorsChart={vendorChart ?? ""}
                classificationsChart={classificationsChart ?? ""}
                location="Location"
                author={author}
              />,
            );

            if (!pdf) {
              setIsGenerating(false);
              messageApi.error("Error generating pdf");
              return;
            }

            const pdfBlob = await generatedPdf.toBlob();

            downloadBlob(pdfBlob, `MonitorReport${new Date().toString()}`);
          } else {
            setIsLoading(false);
            messageApi.error("Error fetching data to download report");
          }

          setIsGenerating(false);
        },
      );
    fetchAll();
  }, [
    vendorsTrigger,
    statsTrigger,
    classificationsTrigger,
    configTrigger,
    setIsGenerating,
    currentUser,
    monitorId,
    messageApi,
  ]);

  return {
    isGenerating,
    isLoading,
    generate,
  };
};
