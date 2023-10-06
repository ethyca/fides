import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features"
import { DictOption, selectAllDictEntries, useGetAllDictionaryEntriesQuery } from "~/features/plus/plus.slice"
import { FidesTable, WrappedCell } from "~/features/common/table";
import { FidesObject } from "~/features/common/table/FidesTable";
import { useMemo } from "react";
import { Column } from "react-table";



type MultipleSystemTable = DictOption & FidesObject

export const AddMultipleSystems = ()=>{


  const features = useFeatures();
  useGetAllDictionaryEntriesQuery(undefined, {
    skip: !features.dictionaryService,
  });

  const dictionaryOptions = useAppSelector(selectAllDictEntries);


  const columns: Column<DictOption>[] = useMemo(
    () => [
      { Header: "System", accessor: "label", Cell: WrappedCell},
    ],
    []
  );

  return (
    <div>
      <FidesTable<MultipleSystemTable> columns={columns} data={dictionaryOptions}/>
    </div>
  )
}