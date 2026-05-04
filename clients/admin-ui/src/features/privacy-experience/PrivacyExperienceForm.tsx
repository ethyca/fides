import {
  Alert,
  Button,
  Checkbox,
  Divider,
  Flex,
  Form,
  formatIsoLocation,
  Icons,
  Input,
  isoStringToEntry,
  Select,
  SelectProps,
  Typography,
  useModal,
} from "fidesui";
import { isEqual } from "lodash";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectLocationsRegulations,
  useGetLocationsRegulationsQuery,
} from "~/features/locations/locations.slice";
import { selectHealth as selectPlusHealth } from "~/features/plus/plus.slice";
import { getSelectedRegionIds } from "~/features/privacy-experience/form/helpers";
import { ExperienceFormInstance } from "~/features/privacy-experience/form/useExperienceForm";
import { selectAllLanguages } from "~/features/privacy-experience/language.slice";
import {
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import {
  selectAllProperties,
  selectPage as selectPropertyPage,
  selectPageSize as selectPropertyPageSize,
  useGetAllPropertiesQuery,
} from "~/features/properties/property.slice";
import {
  ComponentType,
  ConsentMechanism,
  ExperienceConfigCreate,
  ExperienceTranslation,
  Layer1ButtonOption,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeFramework,
  Property,
  RejectAllMechanism,
  ResurfaceBehavior,
  StagedResourceTypeValue,
  SupportedLanguage,
} from "~/types/api";

import { useFeatures } from "../common/features";
import { InfoTooltip } from "../common/InfoTooltip";
import BackButton from "../common/nav/BackButton";
import { useGetConfigurationSettingsQuery } from "../config-settings/config-settings.slice";
import { SwitchField } from "./form/SwitchField";
import { TCFConfigSelect } from "./form/TCFConfigSelect";

// Base component type options without TCF overlay
const baseComponentTypeOptions: SelectProps["options"] = [
  {
    label: "Banner and modal",
    value: ComponentType.BANNER_AND_MODAL,
  },
  {
    label: "Modal",
    value: ComponentType.MODAL,
  },
  {
    label: "Privacy center",
    value: ComponentType.PRIVACY_CENTER,
  },
  {
    label: "Headless",
    value: ComponentType.HEADLESS,
  },
];

// The TCF overlay option to insert
const tcfOverlayOption = {
  label: "TCF overlay",
  value: ComponentType.TCF_OVERLAY,
};

const tcfRejectAllMechanismOptions: SelectProps["options"] = [
  {
    label: "Reject all",
    value: RejectAllMechanism.REJECT_ALL,
  },
  {
    label: "Reject consent only",
    value: RejectAllMechanism.REJECT_CONSENT_ONLY,
  },
];

const resurfaceBehaviorOptions = [
  {
    label: "Reject",
    value: ResurfaceBehavior.REJECT,
    description: "Show the banner again when user rejects",
  },
  {
    label: "Dismiss",
    value: ResurfaceBehavior.DISMISS,
    description: "Show the banner again when user dismisses",
  },
];

const tcfBannerButtonOptions: SelectProps["options"] = [
  {
    label: "Banner and modal",
    value: Layer1ButtonOption.OPT_IN_OPT_OUT,
  },
  {
    label: "Modal only",
    value: Layer1ButtonOption.OPT_IN_ONLY,
  },
];

const bannerButtonOptions: SelectProps["options"] = [
  {
    label: "Opt in/Opt out",
    value: Layer1ButtonOption.OPT_IN_OPT_OUT,
  },
  {
    label: "Acknowledge",
    value: Layer1ButtonOption.ACKNOWLEDGE,
  },
  {
    label: "GPC adaptive",
    value: Layer1ButtonOption.GPC_CONDITIONAL,
  },
];

const GPC_ADAPTIVE_TOOLTIP = `Enabling ${bannerButtonOptions.find((b) => b.value === Layer1ButtonOption.GPC_CONDITIONAL)?.label} will show the acknowledge button when GPC is on, and the opt in/opt out buttons when GPC is off.`;

export const TCF_PLACEHOLDER_ID = "tcf_purposes_placeholder";
const GPP_PLACEHOLDER_ID = "gpp_notices_not_supported_placeholder";
const DISABLED_NOTICE_TOOLTIP =
  "This notice is disabled and will not display. Enable it or remove it from this experience.";

const isGppNotice = (notice: LimitedPrivacyNoticeResponseSchema): boolean => {
  return (
    notice.framework === PrivacyNoticeFramework.GPP_US_NATIONAL ||
    notice.framework === PrivacyNoticeFramework.GPP_US_STATE
  );
};

const filterGppNotices = (
  allNotices: LimitedPrivacyNoticeResponseSchema[],
): LimitedPrivacyNoticeResponseSchema[] => {
  return allNotices.filter((notice) => !isGppNotice(notice));
};

const privacyNoticeIdsWithTcfId = (
  values: ExperienceConfigCreate,
): string[] => {
  if (!values.privacy_notice_ids) {
    return [TCF_PLACEHOLDER_ID];
  }
  if (values.privacy_notice_ids.includes(TCF_PLACEHOLDER_ID)) {
    return values.privacy_notice_ids;
  }
  return [...values.privacy_notice_ids, TCF_PLACEHOLDER_ID];
};

export const PrivacyExperienceForm = ({
  form,
  allPrivacyNotices,
  translationsEnabled,
  onSelectTranslation,
  onCreateTranslation,
  initialValues,
  isSubmitting,
}: {
  form: ExperienceFormInstance;
  allPrivacyNotices: LimitedPrivacyNoticeResponseSchema[];
  translationsEnabled?: boolean;
  onSelectTranslation: (t: ExperienceTranslation) => void;
  onCreateTranslation: (lang: SupportedLanguage) => ExperienceTranslation;
  initialValues: ExperienceConfigCreate;
  isSubmitting: boolean;
}) => {
  const router = useRouter();
  const isPublisherRestrictionsFlagEnabled =
    useFeatures()?.flags?.publisherRestrictions;
  const plusHealth = useAppSelector(selectPlusHealth);

  const component = Form.useWatch("component", form);
  const privacyNoticeIds = Form.useWatch("privacy_notice_ids", form);
  const dismissable = Form.useWatch("dismissable", form);
  const allowVendorAssetDisclosure = Form.useWatch(
    "allow_vendor_asset_disclosure",
    form,
  );
  const resurfaceBehavior = Form.useWatch("resurface_behavior", form);
  // translations is not registered via Form.Item (nested paths conflict with flat
  // registration), so useWatch won't track it. Read directly from the store instead.
  // Re-renders from other useWatch calls (component, etc.) keep this fresh enough.
  const translations = form.getFieldValue("translations") as
    | ExperienceConfigCreate["translations"]
    | undefined;
  const initialComponent = form.getFieldValue("component");

  // antd's built-in pattern: watch all values, then validate without showing
  // errors to derive whether the form is submittable.
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);
  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  // Deep-compare against initial values to detect dirty state. We can't use
  // form.isFieldsTouched() because it doesn't detect programmatic changes
  // (e.g. translation form committing via setFieldsValue).
  const isDirty = useMemo(
    () => !isEqual(form.getFieldsValue(true), initialValues),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- allValues triggers re-eval
    [allValues, initialValues],
  );

  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });

  const { data: appConfig } = useGetConfigurationSettingsQuery({
    api_set: true,
  });

  const allPrivacyNoticesWithTcfPlaceholder: LimitedPrivacyNoticeResponseSchema[] =
    useMemo(() => {
      // Filter out GPP notices for TCF experiences
      const noticesWithTcfPlaceholder = filterGppNotices(allPrivacyNotices);
      const hasFilteredGppNotices =
        noticesWithTcfPlaceholder.length < allPrivacyNotices.length;
      if (!noticesWithTcfPlaceholder.some((n) => n.id === TCF_PLACEHOLDER_ID)) {
        noticesWithTcfPlaceholder.push({
          name: "TCF Purposes",
          id: TCF_PLACEHOLDER_ID,
          notice_key: TCF_PLACEHOLDER_ID,
          data_uses: [],
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
          disabled: false,
        });
      }
      if (hasFilteredGppNotices) {
        noticesWithTcfPlaceholder.push({
          name: "GPP notices not supported in TCF",
          id: GPP_PLACEHOLDER_ID,
          notice_key: GPP_PLACEHOLDER_ID,
          data_uses: [],
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
          disabled: true,
        });
      }
      return noticesWithTcfPlaceholder;
    }, [allPrivacyNotices]);

  const getPrivacyNoticeName = (id: string) => {
    const notice = allPrivacyNotices.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  const getTcfPrivacyNoticeName = (id: string) => {
    let notice = allPrivacyNoticesWithTcfPlaceholder.find((n) => n.id === id);
    if (!notice) {
      // the notice is probably GPP and needs to be listed along with the error message.
      notice = allPrivacyNotices.find((n) => n.id === id);
    }
    return notice?.name ?? id;
  };

  const hasGppNoticesInValues = useMemo(() => {
    if (component === ComponentType.TCF_OVERLAY) {
      return (
        privacyNoticeIds?.some((id: string) => {
          const notice = allPrivacyNotices.find((n) => n.id === id);
          return notice ? isGppNotice(notice) : false;
        }) ?? false
      );
    }
    return false;
  }, [privacyNoticeIds, component, allPrivacyNotices]);

  const filterNoticesForOnlyParentNotices = (
    allNotices: LimitedPrivacyNoticeResponseSchema[],
  ): LimitedPrivacyNoticeResponseSchema[] => {
    const childrenNoticeIds: FlatArray<(string[] | undefined)[], 1>[] =
      allNotices.map((n) => n.children?.map((child) => child.id)).flat();
    return allNotices.filter((n) => !childrenNoticeIds.includes(n.id)) ?? [];
  };

  useGetLocationsRegulationsQuery();
  const locationsRegulations = useAppSelector(selectLocationsRegulations);

  const allSelectedRegions = [
    ...getSelectedRegionIds(locationsRegulations.locations),
    ...getSelectedRegionIds(locationsRegulations.location_groups),
  ];

  const allLanguages = useAppSelector(selectAllLanguages);

  const getTranslationDisplayName = (t: ExperienceTranslation) => {
    const language = allLanguages.find((lang) => lang.id === t.language);
    const name = language ? language.name : t.language;
    return `${name}${t.is_default ? " (Default)" : ""}`;
  };

  const propertyPage = useAppSelector(selectPropertyPage);
  const propertyPageSize = useAppSelector(selectPropertyPageSize);
  useGetAllPropertiesQuery({ page: propertyPage, size: propertyPageSize });
  const allProperties = useAppSelector(selectAllProperties);

  const modal = useModal();

  const handleCancel = () => {
    if (isDirty) {
      modal.confirm({
        title: "Unsaved changes",
        content: "You have unsaved changes. Are you sure you want to leave?",
        okText: "Leave",
        cancelText: "Stay",
        centered: true,
        icon: null,
        onOk: () => router.push(PRIVACY_EXPERIENCE_ROUTE),
      });
    } else {
      router.push(PRIVACY_EXPERIENCE_ROUTE);
    }
  };

  const handleComponentChange = (value: ComponentType) => {
    const newComponent = value as ComponentType;

    // Reset common fields that might need to be unset
    const updates: Partial<ExperienceConfigCreate> = {
      component: value,
      tcf_configuration_id: undefined,
      layer1_button_options: undefined,
      show_layer1_notices: false,
    };

    // Handle TCF specific fields
    if (newComponent !== ComponentType.TCF_OVERLAY) {
      updates.reject_all_mechanism = undefined;
      // Remove TCF placeholder from privacy notices if present
      if (privacyNoticeIds?.includes(TCF_PLACEHOLDER_ID)) {
        updates.privacy_notice_ids = privacyNoticeIds.filter(
          (id: string) => id !== TCF_PLACEHOLDER_ID,
        );
      }
    } else {
      updates.privacy_notice_ids = [TCF_PLACEHOLDER_ID];
    }

    // Set component specific defaults
    switch (newComponent) {
      case ComponentType.PRIVACY_CENTER:
      case ComponentType.HEADLESS:
        updates.dismissable = undefined;
        updates.layer1_button_options = undefined;
        updates.show_layer1_notices = undefined;
        break;
      case ComponentType.BANNER_AND_MODAL:
        updates.layer1_button_options = Layer1ButtonOption.OPT_IN_OPT_OUT;
        break;
      case ComponentType.TCF_OVERLAY:
        updates.layer1_button_options = Layer1ButtonOption.OPT_IN_OPT_OUT;
        updates.reject_all_mechanism = RejectAllMechanism.REJECT_ALL;
        break;
      case ComponentType.MODAL:
        updates.layer1_button_options = undefined;
        updates.show_layer1_notices = undefined;
        break;
      default:
        break;
    }

    // Partial<ExperienceConfigCreate> includes `null` on some fields, but
    // Ant's setFieldsValue types strip `null`. The runtime behavior is correct.
    form.setFieldsValue(updates as Parameters<typeof form.setFieldsValue>[0]);
  };

  // Reactive full-form snapshot for ScrollableList callbacks
  const currentValues = (Form.useWatch([], form) ??
    {}) as ExperienceConfigCreate;

  return (
    <Flex vertical className="min-h-full w-full">
      <Flex vertical className="h-full overflow-y-auto px-4">
        {/* Register fields managed outside of Form.Item (e.g. ScrollableList, conditionally
          rendered switches, translations form) so Form.useWatch and getFieldsValue track them reactively. */}
        <Form.Item name="translations" hidden noStyle>
          <Input />
        </Form.Item>
        <Form.Item name="privacy_notice_ids" hidden noStyle>
          <Input />
        </Form.Item>
        <Form.Item name="regions" hidden noStyle>
          <Input />
        </Form.Item>
        <Form.Item name="properties" hidden noStyle>
          <Input />
        </Form.Item>
        <Form.Item name="resurface_behavior" hidden noStyle>
          <Input />
        </Form.Item>
        <Flex vertical gap="large" className="w-full py-6">
          <div>
            <BackButton
              backPath={PRIVACY_EXPERIENCE_ROUTE}
              onClick={handleCancel}
            />
            <Typography.Title level={5} className="pb-4">
              Configure experience
            </Typography.Title>
            <Form.Item
              name="name"
              label="Name"
              tooltip="Internal admin use only"
              rules={[
                { required: true, message: "Experience name is required" },
              ]}
            >
              <Input data-testid="input-name" />
            </Form.Item>
            <Form.Item
              name="component"
              label="Experience type"
              rules={[
                { required: true, message: "Experience type is required" },
              ]}
            >
              <Select
                options={useMemo(() => {
                  if (plusHealth?.tcf?.enabled) {
                    // Insert TCF overlay as the second item
                    return [
                      baseComponentTypeOptions[0],
                      tcfOverlayOption,
                      ...baseComponentTypeOptions.slice(1),
                    ];
                  }
                  return baseComponentTypeOptions;
                }, [plusHealth])}
                disabled={!!initialComponent}
                onChange={handleComponentChange}
                id="component"
                aria-label="Experience type"
                data-testid="controlled-select-component"
              />
            </Form.Item>
            {component === ComponentType.TCF_OVERLAY &&
              isPublisherRestrictionsFlagEnabled && (
                <TCFConfigSelect
                  overridesEnabled={
                    appConfig?.consent?.override_vendor_purposes
                  }
                />
              )}
            {component === ComponentType.TCF_OVERLAY && (
              <Form.Item
                name="reject_all_mechanism"
                label="Reject all behavior"
                tooltip="Reject all: Blocks both consent and legitimate interest data processing across all purposes, features, and vendors. Reject consent-only: Blocks only consent-based processing, but allows legitimate interest processing to continue, requiring separate objection."
              >
                <Select
                  options={tcfRejectAllMechanismOptions}
                  id="reject_all_mechanism"
                  aria-label="Reject all behavior"
                  data-testid="controlled-select-reject_all_mechanism"
                />
              </Form.Item>
            )}
            {(component === ComponentType.BANNER_AND_MODAL ||
              component === ComponentType.TCF_OVERLAY) && (
              <Form.Item
                name="layer1_button_options"
                label={
                  component === ComponentType.TCF_OVERLAY
                    ? "Reject all visibility"
                    : "Banner options"
                }
                tooltip={
                  component === ComponentType.BANNER_AND_MODAL
                    ? GPC_ADAPTIVE_TOOLTIP
                    : undefined
                }
              >
                <Select
                  options={
                    component === ComponentType.TCF_OVERLAY
                      ? tcfBannerButtonOptions
                      : bannerButtonOptions
                  }
                  id="layer1_button_options"
                  aria-label="Banner options"
                  data-testid="controlled-select-layer1_button_options"
                />
              </Form.Item>
            )}
            {component !== ComponentType.PRIVACY_CENTER &&
              component !== ComponentType.HEADLESS && (
                <SwitchField
                  name="dismissable"
                  label="Allow user to dismiss"
                  className="!mb-0"
                />
              )}
            {(component === ComponentType.BANNER_AND_MODAL ||
              component === ComponentType.TCF_OVERLAY) && (
              <Form.Item
                label="Resurface banner"
                tooltip="Choose when to show the banner again after the user has interacted with it. Leave unchecked for default behavior (only resurface on cookie expiration, vendor changes, and other mandatory updates.)"
                className="!mb-0 mt-4"
              >
                <Checkbox.Group
                  options={resurfaceBehaviorOptions.map((option) => ({
                    label: (
                      <Flex align="center" gap={4}>
                        <Typography.Text strong className="text-xs font-medium">
                          {option.label}
                        </Typography.Text>
                        <InfoTooltip label={option.description} size={14} />
                      </Flex>
                    ),
                    value: option.value,
                    disabled:
                      option.value === ResurfaceBehavior.DISMISS &&
                      !dismissable,
                  }))}
                  value={resurfaceBehavior ?? []}
                  onChange={(checkedValues) => {
                    form.setFieldValue(
                      "resurface_behavior",
                      checkedValues.length > 0 ? checkedValues : null,
                    );
                  }}
                />
              </Form.Item>
            )}
          </div>
          <Divider className="!m-0" />
          <div>
            <Typography.Title level={5} className="pb-4">
              Privacy notices
            </Typography.Title>
            {component === ComponentType.TCF_OVERLAY ? (
              <>
                {hasGppNoticesInValues && (
                  <Alert
                    title="GPP notices are not currently supported in TCF experiences. Please remove any GPP notices from the list below to avoid unexpected behavior."
                    type="error"
                    closable={false}
                    data-testid="gpp-notices-not-supported-alert"
                    className="mb-4"
                  />
                )}
                <ScrollableList<string>
                  addButtonLabel="Add privacy notice"
                  allItems={allPrivacyNoticesWithTcfPlaceholder.map(
                    (n) => n.id,
                  )}
                  values={privacyNoticeIdsWithTcfId(currentValues)}
                  setValues={(newValues) =>
                    form.setFieldValue("privacy_notice_ids", newValues)
                  }
                  canDeleteItem={(item: string): boolean => {
                    return Boolean(item !== TCF_PLACEHOLDER_ID);
                  }}
                  getTooltip={(item: string): string | undefined => {
                    if (item === TCF_PLACEHOLDER_ID) {
                      return "TCF Purposes are required by the framework and cannot be deleted.";
                    }
                    return undefined;
                  }}
                  getWarningTooltip={(id: string): string | undefined => {
                    const notice = allPrivacyNoticesWithTcfPlaceholder.find(
                      (item) => item.id === id,
                    );
                    return notice?.disabled
                      ? DISABLED_NOTICE_TOOLTIP
                      : undefined;
                  }}
                  getItemLabel={getTcfPrivacyNoticeName}
                  draggable={false}
                  baseTestId="privacy-notice"
                  isItemDisabled={(id: string) => {
                    const notice = allPrivacyNoticesWithTcfPlaceholder.find(
                      (n) => n.id === id,
                    );
                    return notice?.disabled ?? false;
                  }}
                  popupMatchSelectWidth={false}
                  selectStyles={{
                    popup: {
                      root: {
                        maxWidth: "500px",
                      },
                    },
                  }}
                />
              </>
            ) : (
              <ScrollableList<string>
                addButtonLabel="Add privacy notice"
                allItems={filterNoticesForOnlyParentNotices(
                  allPrivacyNotices,
                ).map((n) => n.id)}
                values={privacyNoticeIds ?? []}
                setValues={(newValues) =>
                  form.setFieldValue("privacy_notice_ids", newValues)
                }
                getItemLabel={getPrivacyNoticeName}
                draggable={false}
                baseTestId="privacy-notice"
                isItemDisabled={(id: string) => {
                  const notice = allPrivacyNotices.find((n) => n.id === id);
                  return notice?.disabled ?? false;
                }}
                getWarningTooltip={(id: string): string | undefined => {
                  const notice = allPrivacyNotices.find(
                    (item) => item.id === id,
                  );
                  return notice?.disabled ? DISABLED_NOTICE_TOOLTIP : undefined;
                }}
              />
            )}
            {component === ComponentType.BANNER_AND_MODAL &&
              !!privacyNoticeIds?.length && (
                <SwitchField
                  name="show_layer1_notices"
                  label="Add privacy notices to banner"
                  className="!mb-0 pt-6"
                />
              )}
          </div>
          <Divider className="!m-0" />
          <div>
            <Typography.Title level={5} className="pb-4">
              Locations &amp; Languages
            </Typography.Title>
            <ScrollableList
              label="Locations for this experience"
              addButtonLabel="Add location"
              allItems={allSelectedRegions}
              values={form.getFieldValue("regions") ?? []}
              setValues={(newValues) =>
                form.setFieldValue("regions", newValues)
              }
              getItemLabel={(item) => {
                const isoEntry = isoStringToEntry(item);

                return isoEntry
                  ? formatIsoLocation({ isoEntry })
                  : PRIVACY_NOTICE_REGION_RECORD[
                      item
                    ]; /* fallback on internal list for now */
              }}
              draggable
              baseTestId="location"
              popupMatchSelectWidth={false}
            />
            {translationsEnabled ? (
              <>
                <div className="mt-4">
                  <ScrollableList
                    label="Languages for this experience"
                    addButtonLabel="Add language"
                    values={translations ?? []}
                    setValues={(newValues) =>
                      form.setFieldValue("translations", newValues)
                    }
                    idField="language"
                    canDeleteItem={(item) => !item.is_default}
                    allItems={allLanguages
                      .slice()
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((lang) => ({
                        language: lang.id as SupportedLanguage,
                        is_default: false,
                      }))}
                    getItemLabel={getTranslationDisplayName}
                    createNewValue={(opt) =>
                      onCreateTranslation(opt.value as SupportedLanguage)
                    }
                    onEditItem={onSelectTranslation}
                    selectOnAdd
                    draggable
                    baseTestId="language"
                  />
                </div>
                <SwitchField
                  name="auto_detect_language"
                  label="Auto detect language"
                  className="!mb-0 pt-6"
                />
              </>
            ) : (
              <Button
                icon={<Icons.ArrowRight />}
                iconPlacement="end"
                onClick={() => {
                  const t = form.getFieldValue("translations");
                  if (t?.[0]) {
                    onSelectTranslation(t[0]);
                  }
                }}
                data-testid="edit-experience-btn"
              >
                Edit experience text
              </Button>
            )}
          </div>
          <Divider className="!m-0" />
          <div>
            <Typography.Title level={5} style={{ margin: 0 }}>
              Properties
            </Typography.Title>
            <div
              className={
                !form.getFieldValue("properties")?.length ? "mt-4" : undefined
              }
            >
              <ScrollableList
                label="Associated properties"
                addButtonLabel="Add property"
                idField="id"
                nameField="name"
                allItems={allProperties.map((property: Property) => ({
                  id: property.id,
                  name: property.name,
                }))}
                values={form.getFieldValue("properties") ?? []}
                setValues={(newValues) =>
                  form.setFieldValue("properties", newValues)
                }
                draggable
                maxHeight={100}
                baseTestId="property"
                popupMatchSelectWidth={false}
              />
            </div>
          </div>
          {(component === ComponentType.BANNER_AND_MODAL ||
            component === ComponentType.MODAL) && (
            <>
              <Divider className="!m-0" />
              <div>
                <Typography.Title level={5} style={{ margin: 0 }}>
                  Vendors &amp; Assets
                </Typography.Title>
                <SwitchField
                  name="allow_vendor_asset_disclosure"
                  label="Enable vendor disclosure"
                  tooltip="If enabled, the consent banner will include a link beneath privacy notices to view the vendors and assets associated with the notice."
                  className="!mb-0"
                  switchProps={{
                    onChange: (checked) => {
                      if (checked) {
                        // Default selection to Cookie
                        form.setFieldValue("asset_disclosure_include_types", [
                          StagedResourceTypeValue.COOKIE,
                        ]);
                      } else {
                        // Clear values when disabling
                        form.setFieldValue(
                          "asset_disclosure_include_types",
                          [],
                        );
                      }
                      // Re-run validation to immediately reflect changes
                      form.validateFields(["asset_disclosure_include_types"]);
                    },
                  }}
                />
                {!!allowVendorAssetDisclosure && (
                  <Form.Item
                    name="asset_disclosure_include_types"
                    label="Asset types to disclose"
                    tooltip="Select the asset types to disclose. Only cookies are currently supported."
                    dependencies={[
                      "allow_vendor_asset_disclosure",
                      "component",
                    ]}
                    className="!mb-0 pt-6"
                    rules={[
                      {
                        validator: (_, value) => {
                          const allow = form.getFieldValue(
                            "allow_vendor_asset_disclosure",
                          );
                          const comp = form.getFieldValue("component");
                          if (
                            allow &&
                            (comp === ComponentType.BANNER_AND_MODAL ||
                              comp === ComponentType.MODAL)
                          ) {
                            return value?.length
                              ? Promise.resolve()
                              : Promise.reject(
                                  new Error("Select at least one asset type"),
                                );
                          }
                          return Promise.resolve();
                        },
                      },
                    ]}
                  >
                    <Select
                      mode="multiple"
                      id="asset_disclosure_include_types"
                      aria-label="Asset types to disclose"
                      data-testid="controlled-select-asset_disclosure_include_types"
                      options={[
                        {
                          label: StagedResourceTypeValue.COOKIE,
                          value: StagedResourceTypeValue.COOKIE,
                          disabled: false,
                        },
                        {
                          label: StagedResourceTypeValue.BROWSER_REQUEST,
                          value: StagedResourceTypeValue.BROWSER_REQUEST,
                          disabled: true,
                        },
                        {
                          label: StagedResourceTypeValue.I_FRAME,
                          value: StagedResourceTypeValue.I_FRAME,
                          disabled: true,
                        },
                        {
                          label: StagedResourceTypeValue.JAVASCRIPT_TAG,
                          value: StagedResourceTypeValue.JAVASCRIPT_TAG,
                          disabled: true,
                        },
                        {
                          label: StagedResourceTypeValue.IMAGE,
                          value: StagedResourceTypeValue.IMAGE,
                          disabled: true,
                        },
                      ]}
                    />
                  </Form.Item>
                )}
              </div>
            </>
          )}
          <Divider className="!m-0" />
          <div>
            <Typography.Title level={5} style={{ margin: 0 }}>
              Cookie Deletion
            </Typography.Title>
            <Typography.Text className="my-0 mr-1 text-xs">
              Delete rejected cookies on:
            </Typography.Text>
            <SwitchField
              name="cookie_deletion_based_on_host_domain"
              label="Host's domain"
              tooltip="If enabled, deletes user-rejected cookies on the current host domain regardless of the cookie's configured domain. Recommended to enable for ease of consent compliance."
              className="!mb-0"
            />
            <SwitchField
              name="auto_subdomain_cookie_deletion"
              label="Host's subdomain"
              tooltip="If enabled, deletes user-rejected cookies on subdomains in addition to main domain. Recommended to enable for full consent compliance."
              className="!mb-0"
            />
            <SwitchField
              name="configured_domain_cookie_deletion"
              label="Configured domain"
              tooltip="Deletes cookies using the cookie's configured domain. This is enabled by default and not configurable in the admin UI."
              className="!mb-0"
              switchProps={{
                defaultChecked: true,
                disabled: true,
              }}
            />
          </div>
        </Flex>
      </Flex>

      <Flex
        justify="flex-end"
        gap="small"
        className="sticky bottom-0 z-10 px-4 py-2"
        style={{
          borderTop: "1px solid var(--fidesui-color-border)",
          backgroundColor: "var(--fidesui-color-bg-container)",
        }}
      >
        <Button onClick={handleCancel}>Cancel</Button>
        <Button
          htmlType="submit"
          type="primary"
          data-testid="save-btn"
          disabled={isSubmitting || !isDirty || !submittable}
          loading={isSubmitting}
        >
          Save
        </Button>
      </Flex>
    </Flex>
  );
};
export default PrivacyExperienceForm;
