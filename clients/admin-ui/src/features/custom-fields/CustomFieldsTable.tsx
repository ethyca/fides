/* eslint-disable react/no-unstable-nested-components */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton,
  Box,
  BoxProps,
  HStack,
  Text,
  useDisclosure,
  useToast,
  VStack,
} from "fidesui";
import { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  EnableCustomFieldCell,
  FieldTypeCell,
  ResourceTypeCell,
} from "~/features/custom-fields/cells";
import { CustomFieldActions } from "~/features/custom-fields/CustomFieldActions";
import { CustomFieldModal } from "~/features/custom-fields/CustomFieldModal";
import {
  selectAllCustomFieldDefinitions,
  useDeleteCustomFieldDefinitionMutation,
  useGetAllCustomFieldDefinitionsQuery,
} from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId, ScopeRegistryEnum } from "~/types/api";

const ADD_CUSTOM_FIELD_BTN_LABEL = "Add a custom field";

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
    textAlign="center"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        It looks like it’s your first time here!
      </Text>
      <Text fontSize="sm">
        You haven’t created any custom fields yet.
        <br />
        To create a custom field, click on the{" "}
        <strong>&quot;{ADD_CUSTOM_FIELD_BTN_LABEL}&quot;</strong> button
      </Text>
    </VStack>
  </VStack>
);

const columnHelper = createColumnHelper<CustomFieldDefinitionWithId>();

export const CustomFieldsTable = ({ ...rest }: BoxProps): JSX.Element => {
  const toast = useToast();
  const { isLoading } = useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);
  const [deleteCustomFieldDefinitionMutationTrigger] =
    useDeleteCustomFieldDefinitionMutation();
  const { isOpen, onClose, onOpen } = useDisclosure();
  const [activeCustomField, setActiveCustomField] =
    useState<CustomFieldDefinitionWithId>();
  const [globalFilter, setGlobalFilter] = useState<string>();

  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_UPDATE,
  ]);
  const userCanDelete = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_DELETE,
  ]);

  const handleRowClick = (customField: CustomFieldDefinitionWithId) => {
    if (userCanUpdate) {
      setActiveCustomField(customField);
      onOpen();
    }
  };

  const handleDelete = async (customField: CustomFieldDefinitionWithId) => {
    if (userCanDelete && customField.id) {
      const result = await deleteCustomFieldDefinitionMutationTrigger({
        id: customField.id,
      });
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }
      toast(successToastParams("Custom field deleted"));
    }
  };

  const columns: ColumnDef<CustomFieldDefinitionWithId, any>[] = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => (
            <DefaultCell value={props.getValue()} cellProps={props} />
          ),
          header: (props) => <DefaultHeaderCell value="Label" {...props} />,
        }),
        columnHelper.accessor((row) => row.description, {
          id: "description",
          cell: (props) => (
            <DefaultCell value={props.getValue()} cellProps={props} />
          ),
          header: (props) => (
            <DefaultHeaderCell value="Description" {...props} />
          ),
          meta: {
            showHeaderMenu: true,
          },
        }),
        columnHelper.accessor((row) => row.field_type, {
          id: "field_type",
          cell: FieldTypeCell,
          header: (props) => (
            <DefaultHeaderCell value="Field Type" {...props} />
          ),
        }),
        columnHelper.accessor((row) => row.resource_type, {
          id: "resource_type",
          cell: ResourceTypeCell,
          header: (props) => <DefaultHeaderCell value="Locations" {...props} />,
        }),
        userCanUpdate &&
          columnHelper.accessor((row) => row.active, {
            id: "enable",
            cell: EnableCustomFieldCell,
            header: (props) => <DefaultHeaderCell value="Enable" {...props} />,
            meta: { disableRowClick: true },
          }),
        (userCanUpdate || userCanDelete) &&
          columnHelper.display({
            id: "actions",
            header: "Actions",
            cell: ({ row }) => (
              <CustomFieldActions
                customField={row.original}
                onEdit={handleRowClick}
                onDelete={handleDelete}
              />
            ),
            meta: { disableRowClick: true },
          }),
      ].filter(Boolean) as ColumnDef<CustomFieldDefinitionWithId, any>[],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [userCanDelete, userCanUpdate],
  );

  const tableInstance = useReactTable<CustomFieldDefinitionWithId>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: "includesString",
    columns,
    data: customFields,
    state: {
      globalFilter,
    },
    columnResizeMode: "onChange",
  });

  const handleCloseModal = () => {
    setActiveCustomField(undefined);
    onClose();
  };

  const AddCustomFieldButton = () => (
    <Restrict scopes={[ScopeRegistryEnum.CUSTOM_FIELD_DEFINITION_CREATE]}>
      <AntButton
        size="small"
        type="primary"
        data-testid="add-custom-field-btn"
        onClick={onOpen}
      >
        {ADD_CUSTOM_FIELD_BTN_LABEL}
      </AntButton>
    </Restrict>
  );

  return (
    <Box {...rest}>
      <Box maxWidth={600}>
        <Text mb={10} fontSize="sm">
          {customFields.length > 0
            ? "Custom fields enable you to capture metrics specific to your organization and have those metrics appear in the data map and in reports."
            : "Custom fields provide organizations with the capability to capture metrics that are unique to their specific needs, allowing them to create customized reports. These fields can be added to either systems or elements within a taxonomy, and once added, they become reportable fields that are visible on the data map."}
        </Text>
      </Box>
      <Box data-testid="custom-fields-page">
        <TableActionBar>
          <GlobalFilterV2
            globalFilter={globalFilter}
            setGlobalFilter={setGlobalFilter}
            placeholder="Search for a custom field"
          />
          <HStack alignItems="center" spacing={4}>
            <AddCustomFieldButton />
          </HStack>
        </TableActionBar>
        {isLoading ? (
          <Box p={2} borderWidth={1}>
            <TableSkeletonLoader rowHeight={26} numRows={10} />
          </Box>
        ) : (
          <FidesTableV2
            tableInstance={tableInstance}
            onRowClick={userCanUpdate ? handleRowClick : undefined}
            emptyTableNotice={<EmptyTableNotice />}
            enableSorting
          />
        )}
        {isOpen && (
          <CustomFieldModal
            customField={activeCustomField}
            isOpen={isOpen}
            onClose={handleCloseModal}
            isLoading={false}
          />
        )}
      </Box>
    </Box>
  );
};
