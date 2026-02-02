import { Table } from "fidesui";

import { PreferencesSaved } from "~/types/api";

import useTcfConsentTable from "./hooks/useTcfConsentTable";

interface TcfConsentTableProps {
  tcfPreferences?: PreferencesSaved | null;
  loading?: boolean;
}

const TcfConsentTable = ({ tcfPreferences, loading }: TcfConsentTableProps) => {
  const { tableProps, columns } = useTcfConsentTable(tcfPreferences);

  return <Table {...tableProps} columns={columns} loading={loading} />;
};

export default TcfConsentTable;
