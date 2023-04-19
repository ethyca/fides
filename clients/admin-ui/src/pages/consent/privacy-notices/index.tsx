import { PRIVACY_REQUESTS_ROUTE } from "@fidesui/components";
import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Switch,
  Text,
  useDisclosure,
  WarningIcon,
} from "@fidesui/react";
import ConfirmationModal from "common/ConfirmationModal";
import { useHasPermission } from "common/Restrict";
import EmptyTableState from "common/table/EmptyTableState";
import NextLink from "next/link";
import { ChangeEvent, useMemo } from "react";
import { CellProps, Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  PRIVACY_NOTICES_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/v2/routes";
import {
  DateCell,
  FidesTable,
  MechanismCell,
  MultiTagCell,
  TitleCell,
  WrappedCell,
} from "~/features/common/table";
import {
  selectAllPrivacyNotices,
  selectPage,
  selectPageSize,
  useGetAllPrivacyNoticesQuery,
  usePatchPrivacyNoticesMutation,
} from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse, ScopeRegistryEnum } from "~/types/api";

type EnableCellProps<T extends object> = CellProps<T, boolean> & {
  onToggle: (data: any) => Promise<any>;
};

export const EnableCell = <T extends object>({
  value,
  column,
  row,
  onToggle,
}: EnableCellProps<T>) => {
  const modal = useDisclosure();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    // @ts-ignore
    await onToggle([{ id: row.original.id, disabled: !enable }]);
  };

  const handleToggle = async (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
    if (checked) {
      await handlePatch({ enable: true });
    } else {
      modal.onOpen();
    }
  };

  return (
    <>
      <Switch
        colorScheme="complimentary"
        isChecked={!value}
        data-testid={`toggle-${column.Header}`}
        /**
         * It's difficult to use a custom column in react-table 7 since we'd have to modify
         * the declaration file. However, that modifies the type globally, so our datamap table
         * would also have issues. Ignoring the type for now, but should potentially revisit
         * if we update to react-table 8
         * https://github.com/DefinitelyTyped/DefinitelyTyped/discussions/59837
         */
        // @ts-ignore
        disabled={column.disabled}
        onChange={handleToggle}
      />
      <ConfirmationModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        onConfirm={() => {
          handlePatch({ enable: false });
          modal.onClose();
        }}
        title="Disable privacy notice"
        message={
          <Text color="gray.500">
            Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance.
          </Text>
        }
        continueButtonText="Confirm"
        isCentered
        icon={<WarningIcon color="orange.100" />}
      />
    </>
  );
};

const PrivacyNoticesPage = () => {
  // Subscribe to get all privacy notices
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  const { isLoading } = useGetAllPrivacyNoticesQuery({ page, size: pageSize });

  const privacyNotices = useAppSelector(selectAllPrivacyNotices);
  const [patchNoticeMutationTrigger] = usePatchPrivacyNoticesMutation();
  // Permissions
  const userCanUpdate = useHasPermission([
    ScopeRegistryEnum.PRIVACY_NOTICE_UPDATE,
  ]);

  const columns: Column<PrivacyNoticeResponse>[] = useMemo(
    () => [
      {
        Header: "Title",
        accessor: "name",
        Cell: TitleCell,
      },
      {
        Header: "Description",
        accessor: "description",
        Cell: WrappedCell,
      },
      {
        Header: "Mechanism",
        accessor: "consent_mechanism",
        Cell: MechanismCell,
      },
      { Header: "Locations", accessor: "regions", Cell: MultiTagCell },
      { Header: "Created", accessor: "created_at", Cell: DateCell },
      { Header: "Last update", accessor: "updated_at", Cell: DateCell },
      {
        Header: "Enable",
        accessor: "disabled",
        disabled: !userCanUpdate,
        Cell: EnableCell,
        onToggle: patchNoticeMutationTrigger,
      },
    ],
    [patchNoticeMutationTrigger, userCanUpdate]
  );
  return (
    <Layout title="Privacy notices">
      <Box mb={4}>
        <Heading
          fontSize="2xl"
          fontWeight="semibold"
          mb={2}
          data-testid="header"
        >
          Manage privacy notices
        </Heading>
        <Box>
          <Breadcrumb
            fontWeight="medium"
            fontSize="sm"
            color="gray.600"
            data-testid="breadcrumbs"
          >
            <BreadcrumbItem>
              <NextLink href={PRIVACY_REQUESTS_ROUTE}>
                Privacy requests
              </NextLink>
            </BreadcrumbItem>
            {/* TODO: Add Consent breadcrumb once the page exists */}
            <BreadcrumbItem color="complimentary.500">
              <NextLink href={PRIVACY_NOTICES_ROUTE}>Privacy notices</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        Manage the privacy notices and mechanisms that are displayed to your
        users based on their location, what information you collect about them,
        and how you use that data.
      </Text>
      <Box data-testid="privacy-notices-page">
        <FidesTable
          /* @ts-ignore */
          columns={columns}
          data={privacyNotices}
          userCanUpdate={userCanUpdate}
          redirectRoute={PRIVACY_NOTICES_ROUTE}
          createScope={ScopeRegistryEnum.PRIVACY_NOTICE_CREATE}
          addButtonText="Add a privacy notice +"
          addButtonHref={`${PRIVACY_NOTICES_ROUTE}/new`}
          testId="privacy-notice"
          isLoading={isLoading}
          EmptyState={
            <EmptyTableState
              title="To start configuring consent, please first add data uses"
              description="It looks like you have not yet added any data uses to the system. Fides
        relies on how you use data in your organization to provide intelligent
        recommendations and pre-built templates for privacy notices you may need
        to display to your users. To get started with privacy notices, first add
        your data uses to systems on your data map."
              buttonHref={SYSTEM_ROUTE}
              buttonText="Set up data uses"
            />
          }
        />
      </Box>
    </Layout>
  );
};

export default PrivacyNoticesPage;
