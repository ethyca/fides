import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Alert,
  Button,
  Flex,
  Form,
  FormRule,
  Input,
  Select,
  Switch,
  Typography,
  useMessage,
} from "fidesui";
import { isEqual } from "lodash";
import { useEffect, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  CustomFieldsList,
  useCustomFields,
} from "~/features/common/custom-fields";
import { LegacyResourceTypes } from "~/features/common/custom-fields/types";
import { useFeatures } from "~/features/common/features/features.slice";
import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  isFetchBaseQueryError,
  VendorSources,
} from "~/features/common/helpers";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import { useHasPermission } from "~/features/common/Restrict";
import DatasetSelectOption from "~/features/dataset/DatasetSelectOption";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
  useLazyGetDictionaryDataUsesQuery,
} from "~/features/plus/plus.slice";
import {
  selectLockedForGVL,
  setLockedForGVL,
  setSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import {
  DictSuggestionNumberInput,
  DictSuggestionSwitch,
  DictSuggestionTextArea,
  DictSuggestionTextInput,
} from "~/features/system/dictionary-form/DictSuggestionInputs";
import { transformDictDataUseToDeclaration } from "~/features/system/dictionary-form/helpers";
import {
  defaultInitialValues,
  FormValues,
  transformFormValuesToSystem,
  transformSystemToFormValues,
} from "~/features/system/form";
import { usePrivacyDeclarationData } from "~/features/system/privacy-declarations/hooks";
import {
  useBulkAssignStewardMutation,
  useCreateSystemMutation,
  useGetAllSystemsQuery,
  useLazyGetSystemByFidesKeyQuery,
  useLazyGetSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system/system.slice";
import { usePopulateSystemAssetsMutation } from "~/features/system/system-assets.slice";
import { useGetAllSystemGroupsQuery } from "~/features/system/system-groups.slice";
import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";
import {
  legalBasisForProfilingOptions,
  legalBasisForTransferOptions,
  responsibilityOptions,
} from "~/features/system/SystemInformationFormSelectOptions";
import VendorSelector from "~/features/system/VendorSelector";
import {
  useGetAllUsersQuery,
  useRemoveUserManagedSystemMutation,
} from "~/features/user-management";
import { ScopeRegistryEnum, SystemResponse } from "~/types/api";

import { formatUser } from "../common/utils";

interface Props {
  onSuccess: (system: SystemResponse) => void;
  system?: SystemResponse;
  children?: React.ReactNode;
}

const SystemInformationForm = ({
  onSuccess,
  system: passedInSystem,
  children,
}: Props) => {
  const [form] = Form.useForm<FormValues>();
  const { data: systems = [] } = useGetAllSystemsQuery();
  const features = useFeatures();
  const { plus: systemGroupsEnabled, rbac: isRbacEnabled } = features;

  const canUpdateSystems = useHasPermission([
    ScopeRegistryEnum.SYSTEM_UPDATE,
    ScopeRegistryEnum.SYSTEM_MANAGER_UPDATE,
  ]);
  const isReadOnly = isRbacEnabled && passedInSystem && !canUpdateSystems;

  const dispatch = useAppDispatch();

  const { data: eligibleUsersData } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    include_external: false,
    exclude_approvers: true,
  });

  const dataStewardOptions = useMemo(() => {
    const users = eligibleUsersData?.items || [];
    return users.map((user) => ({
      label: formatUser(user),
      value: user.username,
    }));
  }, [eligibleUsersData]);

  const customFields = useCustomFields({
    resourceType: LegacyResourceTypes.SYSTEM,
    resourceFidesKey: passedInSystem?.fides_key,
  });

  const { ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: true,
    includeDisabled: false,
  });

  const initialValues = useMemo(
    () =>
      passedInSystem
        ? transformSystemToFormValues(
            passedInSystem,
            customFields.customFieldValues,
          )
        : defaultInitialValues,
    [passedInSystem, customFields.customFieldValues],
  );

  const [getSystemQueryTrigger] = useLazyGetSystemsQuery();

  const nameUniquenessRule: FormRule = useMemo(
    () => ({
      validator: async (_, value) => {
        if (!value) {
          return Promise.resolve();
        }
        const { data } = await getSystemQueryTrigger({
          page: 1,
          size: 10,
          search: value,
        });
        const systemResults = data?.items || [];
        const similarSystemNames = systemResults.filter(
          (s) => s.name !== initialValues.name,
        );
        if (similarSystemNames.some((s) => s.name === value)) {
          return Promise.reject(
            new Error(
              `You already have a system called "${value}". Please specify a unique name for this system.`,
            ),
          );
        }
        return Promise.resolve();
      },
    }),
    [getSystemQueryTrigger, initialValues.name],
  );

  const [createSystemMutationTrigger, createSystemMutationResult] =
    useCreateSystemMutation();
  const [updateSystemMutationTrigger, updateSystemMutationResult] =
    useUpdateSystemMutation();
  const [bulkAssignSteward] = useBulkAssignStewardMutation();
  const [populateSystemAssets] = usePopulateSystemAssetsMutation();
  const [getSystemByFidesKey] = useLazyGetSystemByFidesKeyQuery();
  const [removeUserManagedSystem] = useRemoveUserManagedSystemMutation();
  useGetAllDictionaryEntriesQuery(undefined, {
    skip: !features.dictionaryService,
  });
  const [getDictionaryDataUseTrigger] = useLazyGetDictionaryDataUsesQuery();

  const { data: allSystemGroups } = useGetAllSystemGroupsQuery(undefined, {
    skip: !systemGroupsEnabled,
  });

  const systemGroupOptions = useMemo(
    () =>
      allSystemGroups?.map((group) => ({
        value: group.fides_key,
        label: group.name,
      })) || [],
    [allSystemGroups],
  );

  const dictionaryOptions = useAppSelector(selectAllDictEntries);
  const lockedForGVL = useAppSelector(selectLockedForGVL);

  const isEditing = useMemo(
    () =>
      Boolean(
        passedInSystem &&
        systems?.some((s) => s.fides_key === passedInSystem?.fides_key),
      ),
    [passedInSystem, systems],
  );

  const datasetSelectOptions = useMemo(
    () =>
      dataProps.allDatasets
        ? dataProps.allDatasets.map((ds) => ({
            value: ds.fides_key,
            label: ds.name ? ds.name : ds.fides_key,
          }))
        : [],
    [dataProps.allDatasets],
  );

  const message = useMessage();
  const { Text } = Typography;

  // Fall back to initialValues when the watch is still undefined (first render
  // before the form publishes its state, or transient undefineds during the
  // dict-suggestion show/hide lifecycle) so conditional sections don't blink
  // out and unmount.
  const processesPersonalData =
    Form.useWatch("processes_personal_data", form) ??
    initialValues.processes_personal_data;
  const exemptFromPrivacyRegulations =
    Form.useWatch("exempt_from_privacy_regulations", form) ??
    initialValues.exempt_from_privacy_regulations;
  const usesProfiling =
    Form.useWatch("uses_profiling", form) ?? initialValues.uses_profiling;
  const doesInternationalTransfers =
    Form.useWatch("does_international_transfers", form) ??
    initialValues.does_international_transfers;
  const requiresDpas =
    Form.useWatch("requires_data_protection_assessments", form) ??
    initialValues.requires_data_protection_assessments;
  const fidesKey = Form.useWatch("fides_key", form);

  // Custom field values load asynchronously after the form mounts; once they're
  // available, push them into the form so the registered Form.Items pick them
  // up. Only relevant in edit mode (create mode has no pre-existing values).
  useEffect(() => {
    if (passedInSystem && !customFields.isLoading) {
      form.setFieldsValue({
        customFieldValues: customFields.customFieldValues,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customFields.isLoading, customFields.customFieldValues]);

  const handleSubmit = async (submittedValues: FormValues) => {
    // antd's onFinish only includes registered Form.Item fields; merge with
    // initialValues so non-rendered fields (privacy_declarations,
    // system_type, etc.) make it into the payload.
    const values: FormValues = { ...initialValues, ...submittedValues };
    let dictionaryDeclarations;
    if (values.vendor_id && (values.privacy_declarations?.length ?? 0) === 0) {
      const dataUseQueryResult = await getDictionaryDataUseTrigger({
        vendor_id: values.vendor_id!,
      });
      if (dataUseQueryResult.isError) {
        const isNotFoundError =
          isFetchBaseQueryError(dataUseQueryResult.error) &&
          dataUseQueryResult.error.status === 404;
        if (!isNotFoundError) {
          const dataUseErrorMsg = getErrorMessage(
            dataUseQueryResult.error,
            `A problem occurred while fetching data uses from Fides Compass for your system.  Please try again.`,
          );
          message.error(dataUseErrorMsg);
        }
      } else if (
        dataUseQueryResult.data &&
        dataUseQueryResult.data.items.length > 0
      ) {
        dictionaryDeclarations = dataUseQueryResult.data.items.map((dec) => ({
          ...transformDictDataUseToDeclaration(dec),
          name: dec.name ?? "",
        }));
      }
    }

    const valuesToSubmit = {
      ...values,
      privacy_declarations:
        dictionaryDeclarations ?? values.privacy_declarations,
    };

    const systemBody = transformFormValuesToSystem(valuesToSubmit);

    const handleResult = (
      result:
        | { data: SystemResponse }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const attemptedAction = isEditing ? "editing" : "creating";
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while ${attemptedAction} the system. Please try again.`,
        );
        message.error(errorMsg);
      } else {
        message.destroy();
        onSuccess(result.data);
        dispatch(setSuggestions("initial"));
      }
    };

    let result:
      | { data: SystemResponse }
      | { error: FetchBaseQueryError | SerializedError };
    if (isEditing) {
      result = await updateSystemMutationTrigger(systemBody);
    } else {
      result = await createSystemMutationTrigger(systemBody);
    }

    await customFields.upsertCustomFields(values);

    if (
      !isEditing &&
      values.vendor_id &&
      !isErrorResult(result) &&
      result.data?.fides_key
    ) {
      const assetResult = await populateSystemAssets({
        systemKey: result.data.fides_key,
      });
      if (isErrorResult(assetResult)) {
        message.error(
          "An unexpected error occurred while populating the system assets from Compass. Please try again.",
        );
      }
    }

    if (!isErrorResult(result) && result.data?.fides_key) {
      const systemData = result.data;
      const currentStewardsMap = new Map(
        (systemData.data_stewards || []).map(
          (user: { username: string; id: string }) => [user.username, user.id],
        ),
      );
      const currentStewards = Array.from(currentStewardsMap.keys());
      const desiredStewards = values.data_stewards || [];

      const stewardsToAdd = desiredStewards.filter(
        (steward) => !currentStewards.includes(steward),
      );

      const stewardsToRemove = currentStewards.filter(
        (steward: string) => !desiredStewards.includes(steward),
      );

      await Promise.all(
        stewardsToAdd.map(async (steward) => {
          const assignResult = await bulkAssignSteward({
            data_steward: steward,
            system_keys: [systemData.fides_key],
          });
          if (isErrorResult(assignResult)) {
            message.warning(
              `Failed to assign ${steward} as data steward. ${getErrorMessage(
                assignResult.error,
                "Please try again.",
              )}`,
            );
          }
        }),
      );

      await Promise.all(
        stewardsToRemove
          .map((steward) => {
            const stewardId = currentStewardsMap.get(steward);
            if (!stewardId) {
              message.warning(
                `Could not find user ID for ${steward}. Skipping removal.`,
              );
              return null;
            }
            return { steward, stewardId };
          })
          .filter(
            (item): item is { steward: string; stewardId: string } =>
              item !== null,
          )
          .map(async ({ steward, stewardId }) => {
            const removeResult = await removeUserManagedSystem({
              userId: stewardId,
              systemKey: systemData.fides_key,
            });
            if (isErrorResult(removeResult)) {
              message.warning(
                `Failed to remove ${steward} as data steward. ${getErrorMessage(
                  removeResult.error,
                  "Please try again.",
                )}`,
              );
            }
          }),
      );

      if (stewardsToAdd.length > 0 || stewardsToRemove.length > 0) {
        const refreshedSystemResult = await getSystemByFidesKey(
          systemData.fides_key,
        );
        if (
          refreshedSystemResult &&
          "data" in refreshedSystemResult &&
          refreshedSystemResult.data &&
          !("error" in refreshedSystemResult)
        ) {
          result.data = refreshedSystemResult.data as SystemResponse;
        }
      }
    }

    handleResult(result);
  };

  const handleVendorSelected = (newVendorId?: string | null) => {
    if (!features.dictionaryService) {
      return;
    }
    if (!newVendorId) {
      dispatch(setSuggestions("hiding"));
      dispatch(setLockedForGVL(false));
      return;
    }
    dispatch(setSuggestions("showing"));
    if (
      features.tcf &&
      extractVendorSource(newVendorId) === VendorSources.GVL
    ) {
      dispatch(setLockedForGVL(true));
    } else {
      dispatch(setLockedForGVL(false));
    }
  };

  const isLoading =
    updateSystemMutationResult.isLoading ||
    createSystemMutationResult.isLoading ||
    customFields.isLoading;

  return (
    <Form
      form={form}
      initialValues={initialValues}
      onFinish={handleSubmit}
      layout="vertical"
      key={passedInSystem?.fides_key ?? "create"}
    >
      <Form.Item shouldUpdate noStyle>
        {() => (
          <FormGuard
            id="SystemInfoTab"
            name="System Info"
            isDirty={!isEqual(form.getFieldsValue(true), initialValues)}
          />
        )}
      </Form.Item>
      {isReadOnly && (
        <Alert
          title="Read-only access"
          description="You have read-only access to this system. Contact an administrator if you need to make changes."
          type="info"
          showIcon
          className="mb-4"
        />
      )}
      <fieldset disabled={isReadOnly} className="border-0 p-0">
        <Flex vertical className="w-full lg:max-w-[70%]">
          <Text>
            Adding appropriate detail and context to each system helps everyone
            understand the tech stack better and makes reporting easier.
          </Text>

          <SystemFormInputGroup heading="System details">
            {features.dictionaryService ? (
              <VendorSelector
                label="System name"
                options={dictionaryOptions}
                onVendorSelected={handleVendorSelected}
                isCreate={!passedInSystem}
                lockedForGVL={lockedForGVL}
                nameRules={[
                  { required: true, message: "System name is required" },
                  nameUniquenessRule,
                ]}
              />
            ) : (
              <Form.Item
                name="name"
                label="System name"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                required
                rules={[
                  { required: true, message: "System name is required" },
                  nameUniquenessRule,
                ]}
              >
                <Input id="name" data-testid="input-name" />
              </Form.Item>
            )}
            {passedInSystem?.fides_key && (
              <Form.Item
                name="fides_key"
                label="Unique ID"
                tooltip="An auto-generated unique ID based on the system name"
              >
                <Input id="fides_key" disabled data-testid="input-fides_key" />
              </Form.Item>
            )}
            <DictSuggestionTextArea
              id="description"
              name="description"
              label="Description"
              tooltip="What services does this system perform?"
            />
            <Form.Item
              name="tags"
              label="System Tags"
              tooltip="Are there any tags to associate with this system?"
            >
              <Select
                id="tags"
                mode="tags"
                aria-label="System Tags"
                options={
                  initialValues.tags
                    ? initialValues.tags.map((s) => ({ value: s, label: s }))
                    : []
                }
                data-testid="controlled-select-tags"
              />
            </Form.Item>
            {systemGroupsEnabled && (
              <Form.Item
                name="system_groups"
                label="System groups"
                tooltip="Which system groups are associated with this system?"
              >
                <Select
                  mode="multiple"
                  aria-label="System groups"
                  options={systemGroupOptions}
                  data-testid="controlled-select-system_groups"
                />
              </Form.Item>
            )}
          </SystemFormInputGroup>

          <SystemFormInputGroup heading="Dataset reference">
            <Form.Item
              name="dataset_references"
              label="Dataset references"
              tooltip="Is there a dataset configured for this system?"
            >
              <Select
                mode="multiple"
                aria-label="Dataset references"
                options={datasetSelectOptions}
                optionRender={DatasetSelectOption}
                data-testid="controlled-select-dataset_references"
              />
            </Form.Item>
          </SystemFormInputGroup>

          <SystemFormInputGroup heading="Data processing properties">
            <Flex vertical>
              <div className="mb-4">
                <DictSuggestionSwitch
                  name="processes_personal_data"
                  label="This system processes personal data"
                  tooltip="Does this system process personal data?"
                  disabled={lockedForGVL}
                />
              </div>
              <div className="rounded bg-gray-50 p-4">
                <Flex vertical>
                  <DictSuggestionSwitch
                    name="exempt_from_privacy_regulations"
                    label="This system is exempt from privacy regulations"
                    tooltip="Is this system exempt from privacy regulations?"
                    disabled={!processesPersonalData || lockedForGVL}
                  />
                  {exemptFromPrivacyRegulations && (
                    <div className="mt-4">
                      <Form.Item
                        name="reason_for_exemption"
                        label="Reason for exemption"
                        tooltip="Why is this system exempt from privacy regulation?"
                        required={exemptFromPrivacyRegulations}
                      >
                        <Input
                          disabled={lockedForGVL}
                          data-testid="input-reason_for_exemption"
                        />
                      </Form.Item>
                    </div>
                  )}
                </Flex>
              </div>
              {processesPersonalData && !exemptFromPrivacyRegulations && (
                <Flex vertical className="mt-4 gap-4">
                  <Flex vertical>
                    <DictSuggestionSwitch
                      name="uses_profiling"
                      label="This system performs profiling"
                      tooltip="Does this system perform profiling that could have a legal effect?"
                      disabled={lockedForGVL}
                    />
                    {usesProfiling && (
                      <div className="mt-4">
                        <Form.Item
                          name="legal_basis_for_profiling"
                          label="Legal basis for profiling"
                          tooltip="What is the legal basis under which profiling is performed?"
                          required={usesProfiling}
                        >
                          <Select
                            mode="multiple"
                            aria-label="Legal basis for profiling"
                            options={legalBasisForProfilingOptions}
                            disabled={lockedForGVL}
                            data-testid="controlled-select-legal_basis_for_profiling"
                          />
                        </Form.Item>
                      </div>
                    )}
                  </Flex>
                  <Flex vertical>
                    <DictSuggestionSwitch
                      name="does_international_transfers"
                      label="This system transfers data"
                      tooltip="Does this system transfer data to other countries or international organizations?"
                      disabled={lockedForGVL}
                    />
                    {doesInternationalTransfers && (
                      <div className="mt-4">
                        <Form.Item
                          name="legal_basis_for_transfers"
                          label="Legal basis for transfer"
                          tooltip="What is the legal basis under which the data is transferred?"
                          required={doesInternationalTransfers}
                        >
                          <Select
                            mode="multiple"
                            aria-label="Legal basis for transfer"
                            options={legalBasisForTransferOptions}
                            disabled={lockedForGVL}
                            data-testid="controlled-select-legal_basis_for_transfers"
                          />
                        </Form.Item>
                      </div>
                    )}
                  </Flex>
                  <Flex vertical>
                    <Form.Item
                      name="requires_data_protection_assessments"
                      label="This system requires Data Privacy Assessments"
                      tooltip="Does this system require (DPA/DPIA) assessments?"
                      layout="horizontal"
                      colon={false}
                      valuePropName="checked"
                      className="mb-0"
                    >
                      <Switch
                        size="small"
                        disabled={lockedForGVL}
                        data-testid="input-requires_data_protection_assessments"
                      />
                    </Form.Item>
                    {requiresDpas && (
                      <div className="mt-4">
                        <Form.Item
                          name="dpa_location"
                          label="DPIA/DPA location"
                          tooltip="Where is the DPA/DPIA stored?"
                          required={requiresDpas}
                        >
                          <Input
                            disabled={lockedForGVL}
                            data-testid="input-dpa_location"
                          />
                        </Form.Item>
                      </div>
                    )}
                  </Flex>
                </Flex>
              )}
            </Flex>
          </SystemFormInputGroup>

          {processesPersonalData && !exemptFromPrivacyRegulations && (
            <>
              <SystemFormInputGroup heading="Cookie properties">
                <DictSuggestionSwitch
                  name="uses_cookies"
                  label="This system uses cookies"
                  tooltip="Does this system use cookies?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionSwitch
                  name="cookie_refresh"
                  label="This system refreshes cookies"
                  tooltip="Does this system automatically refresh cookies?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionSwitch
                  name="uses_non_cookie_access"
                  label="This system uses non-cookie trackers"
                  tooltip="Does this system use other types of trackers?"
                  disabled={lockedForGVL}
                />
                <DictSuggestionNumberInput
                  name="cookie_max_age_seconds"
                  label="Maximum duration (seconds)"
                  tooltip="What is the maximum amount of time a cookie will live?"
                  disabled={lockedForGVL}
                />
              </SystemFormInputGroup>

              <SystemFormInputGroup heading="Administrative properties">
                <Form.Item
                  name="data_stewards"
                  label="Data stewards"
                  tooltip="Who are the stewards assigned to the system?"
                >
                  <Select
                    mode="multiple"
                    aria-label="Data stewards"
                    options={dataStewardOptions}
                    showSearch
                    filterOption={(input, option) =>
                      String(option?.label ?? "")
                        .toLowerCase()
                        .includes(input.toLowerCase())
                    }
                    placeholder="Select data stewards"
                    data-testid="controlled-select-data_stewards"
                  />
                </Form.Item>
                <DictSuggestionTextInput
                  id="privacy_policy"
                  name="privacy_policy"
                  label="Privacy policy URL"
                  tooltip="Where can the privacy policy be located?"
                  disabled={lockedForGVL}
                  rules={[
                    {
                      type: "url",
                      message: "Privacy policy must be a valid URL",
                    },
                  ]}
                />
                <DictSuggestionTextInput
                  id="legal_name"
                  name="legal_name"
                  label="Legal name"
                  tooltip="What is the legal name of the business?"
                />
                <DictSuggestionTextArea
                  id="legal_address"
                  name="legal_address"
                  label="Legal address"
                  tooltip="What is the legal address for the business?"
                />
                <Form.Item
                  name="administrating_department"
                  label="Department"
                  tooltip="Which department is concerned with this system?"
                >
                  <Input
                    disabled={
                      !processesPersonalData || exemptFromPrivacyRegulations
                    }
                    data-testid="input-administrating_department"
                  />
                </Form.Item>
                <Form.Item
                  name="responsibility"
                  label="Responsibility"
                  tooltip="What is the role of the business with regard to data processing?"
                >
                  <Select
                    mode="multiple"
                    aria-label="Responsibility"
                    options={responsibilityOptions}
                    disabled={
                      !processesPersonalData || exemptFromPrivacyRegulations
                    }
                    data-testid="controlled-select-responsibility"
                  />
                </Form.Item>
                <DictSuggestionTextInput
                  name="dpo"
                  id="dpo"
                  label="Legal contact (DPO)"
                  tooltip="What is the official privacy contact information?"
                  disabled={lockedForGVL}
                />
                <Form.Item
                  name="joint_controller_info"
                  label="Joint controller"
                  tooltip="Who are the party or parties that share responsibility for processing data?"
                >
                  <Input
                    disabled={
                      !processesPersonalData || exemptFromPrivacyRegulations
                    }
                    data-testid="input-joint_controller_info"
                  />
                </Form.Item>
                <DictSuggestionTextInput
                  label="Data security practices"
                  name="data_security_practices"
                  id="data_security_practices"
                  tooltip="Which data security practices are employed to keep the data safe?"
                />
                <DictSuggestionTextInput
                  label="Legitimate interest disclosure URL"
                  name="legitimate_interest_disclosure_url"
                  id="legitimate_interest_disclosure_url"
                  disabled={lockedForGVL}
                />
                <DictSuggestionTextInput
                  label="Vendor deleted date"
                  name="vendor_deleted_date"
                  id="vendor_deleted_date"
                  tooltip="If this vendor is no longer active, it will be 'soft' deleted. When that occurs, it's deleted date will be recorded here for reporting."
                  disabled
                />
              </SystemFormInputGroup>
              {fidesKey ? (
                <CustomFieldsList
                  resourceType={LegacyResourceTypes.SYSTEM}
                  resourceFidesKey={fidesKey}
                />
              ) : null}
            </>
          )}
        </Flex>
      </fieldset>
      {!isReadOnly && (
        <div className="mt-6">
          <Form.Item shouldUpdate noStyle>
            {() => {
              // Deep-compare instead of form.isFieldsTouched(): VendorSelector
              // and the dict-suggestion fields commit values via setFieldsValue,
              // which doesn't mark fields as touched.
              const isDirty = !isEqual(
                form.getFieldsValue(true),
                initialValues,
              );
              const hasErrors = form
                .getFieldsError()
                .some(({ errors }) => errors.length > 0);
              return (
                <Button
                  htmlType="submit"
                  type="primary"
                  disabled={isLoading || !isDirty || hasErrors}
                  loading={isLoading}
                  data-testid="save-btn"
                >
                  Save
                </Button>
              );
            }}
          </Form.Item>
        </div>
      )}
      {children}
    </Form>
  );
};

export default SystemInformationForm;
