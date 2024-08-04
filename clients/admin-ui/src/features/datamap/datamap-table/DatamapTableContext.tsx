import { Table } from "@tanstack/react-table";
import React from "react";

import { DatamapRow } from "../datamap.slice";

type DatamapTableInstance = Table<DatamapRow>;

export class DatamapTableContextValue {
  tableInstance: DatamapTableInstance | null;

  constructor(tableInstance: DatamapTableInstance | null = null) {
    this.tableInstance = tableInstance;
    this.updateTableInstance = this.updateTableInstance.bind(this);
  }

  updateTableInstance(tableInstance: DatamapTableInstance) {
    this.tableInstance = tableInstance;
  }
}

const DatamapTableContext = React.createContext<DatamapTableContextValue>(
  new DatamapTableContextValue(),
);

export default DatamapTableContext;
