import { createContext } from "react";

export interface DatasetEditorActions {
  addCollection: () => void;
  /** Add a field. If parentFieldPath is provided, adds a nested sub-field. */
  addField: (collectionName: string, parentFieldPath?: string) => void;
  deleteCollection: (collectionName: string) => void;
  deleteField: (collectionName: string, fieldPath: string) => void;
}

const DatasetEditorActionsContext = createContext<DatasetEditorActions>({
  addCollection: () => {},
  addField: () => {},
  deleteCollection: () => {},
  deleteField: () => {},
});

export default DatasetEditorActionsContext;
