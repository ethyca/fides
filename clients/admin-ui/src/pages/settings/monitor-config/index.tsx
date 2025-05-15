import { AntSpin } from "fidesui";
import Link from "next/link";

import Layout from "~/features/common/Layout";
import {
  CREATE_MONITOR_CONFIG_ROUTE,
  MONITOR_CONFIG_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";

const MonitorConfigTable = () => {
  const { data, isLoading } = useGetSharedMonitorConfigsQuery({
    page: 1,
    size: 10,
  });

  return (
    <Layout title="Monitor configs">
      <PageHeader
        heading="Monitor configs"
        breadcrumbItems={[
          {
            title: "All configs",
          },
        ]}
      />
      {isLoading ? (
        <AntSpin
          size="large"
          className="flex h-full items-center justify-center"
        />
      ) : (
        <div>
          <Link href={CREATE_MONITOR_CONFIG_ROUTE}>Add new</Link>
          <ul>
            {data?.items?.map((config) => (
              <li key={config.id}>
                <Link href={`${MONITOR_CONFIG_ROUTE}/${config.id}`}>
                  {config.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Layout>
  );
};
export default MonitorConfigTable;
