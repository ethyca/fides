import React from "react";
import { TableInstance } from "react-table";

import { DatamapRow } from "../datamap.slice";

export class DatamapTableContextValue {
  tableInstance: TableInstance<DatamapRow> | null;

  constructor(tableInstance: TableInstance<DatamapRow> | null = null) {
    this.tableInstance = tableInstance;
    this.updateTableInstance = this.updateTableInstance.bind(this);
  }

  updateTableInstance(tableInstance: TableInstance<DatamapRow>) {
    this.tableInstance = tableInstance;
  }
}

const DatamapTableContext = React.createContext<DatamapTableContextValue>(
  new DatamapTableContextValue()
);

export default DatamapTableContext;
