import {
  AntButton as Button,
  AntSelectProps as SelectProps,
  AntTooltip as Tooltip,
  ArrowForwardIcon,
  Box,
  Collapse,
  Divider,
  Flex,
  Heading,
  Text,
} from "fidesui";
import { useFormikContext } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { CustomSwitch, CustomTextInput } from "~/features/common/form/inputs";
import BackButton from "~/features/common/nav/BackButton";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectTCFConfigFilters,
  useGetTCFConfigurationsQuery,
} from "~/features/consent-settings/tcf/tcf-config.slice";
import {
  selectLocationsRegulations,
  useGetLocationsRegulationsQuery,
} from "~/features/locations/locations.slice";
import { getSelectedRegionIds } from "~/features/privacy-experience/form/helpers";
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
  Property,
  RejectAllMechanism,
  SupportedLanguage,
} from "~/types/api";

import { ControlledSelect } from "../common/form/ControlledSelect";
import { useGetConfigurationSettingsQuery } from "../config-settings/config-settings.slice";

const componentTypeOptions: SelectProps["options"] = [
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

const tcfRejectAllMechanismOptions: SelectProps["options"] = [
  {
    label: "Reject All",
    value: RejectAllMechanism.REJECT_ALL,
  },
  {
    label: "Reject Consent Only",
    value: RejectAllMechanism.REJECT_CONSENT_ONLY,
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
    label: "Opt In/Opt Out",
    value: Layer1ButtonOption.OPT_IN_OPT_OUT,
  },
  {
    label: "Acknowledge",
    value: Layer1ButtonOption.ACKNOWLEDGE,
  },
];

const TCF_PLACEHOLDER_ID = "tcf_purposes_placeholder";

export const PrivacyExperienceConfigColumnLayout = ({
  buttonPanel,
  children,
}: {
  buttonPanel: React.ReactNode;
  children: React.ReactNode;
}) => (
  <Flex direction="column" minH="full" w="25%" borderRight="1px solid #DEE5EE">
    <Flex direction="column" h="full" overflowY="auto" px={4}>
      <Flex direction="column" gap={4} w="full" pb={4}>
        {children}
      </Flex>
    </Flex>
    {buttonPanel}
  </Flex>
);

function privacyNoticeIdsWithTcfId(values: ExperienceConfigCreate): string[] {
  if (!values.privacy_notice_ids) {
    return [TCF_PLACEHOLDER_ID];
  }
  const noticeIdsWithTcfId = values.privacy_notice_ids;
  if (!noticeIdsWithTcfId.includes(TCF_PLACEHOLDER_ID)) {
    noticeIdsWithTcfId.push(TCF_PLACEHOLDER_ID);
  }
  return noticeIdsWithTcfId;
}

export const PrivacyExperienceForm = ({
  allPrivacyNotices,
  translationsEnabled,
  onSelectTranslation,
  onCreateTranslation,
}: {
  allPrivacyNotices: LimitedPrivacyNoticeResponseSchema[];
  translationsEnabled?: boolean;
  onSelectTranslation: (t: ExperienceTranslation) => void;
  onCreateTranslation: (lang: SupportedLanguage) => ExperienceTranslation;
}) => {
  const router = useRouter();

  const { values, setFieldValue, dirty, isValid, isSubmitting, initialValues } =
    useFormikContext<ExperienceConfigCreate>();
  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });

  const { data: appConfig } = useGetConfigurationSettingsQuery({
    api_set: true,
  });

  const allPrivacyNoticesWithTcfPlaceholder: LimitedPrivacyNoticeResponseSchema[] =
    useMemo(() => {
      const noticesWithTcfPlaceholder = [...allPrivacyNotices];
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
      return noticesWithTcfPlaceholder;
    }, [allPrivacyNotices]);

  const getPrivacyNoticeName = (id: string) => {
    const notice = allPrivacyNoticesWithTcfPlaceholder.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  const filterNoticesForOnlyParentNotices = (
    allNotices: LimitedPrivacyNoticeResponseSchema[],
  ): LimitedPrivacyNoticeResponseSchema[] => {
    const childrenNoticeIds: FlatArray<(string[] | undefined)[], 1>[] =
      allNotices.map((n) => n.children?.map((child) => child.id)).flat();
    return (
      allPrivacyNotices.filter((n) => !childrenNoticeIds.includes(n.id)) ?? []
    );
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

  const tcfConfigFilters = useAppSelector(selectTCFConfigFilters);
  const { data: tcfConfigs } = useGetTCFConfigurationsQuery(tcfConfigFilters);

  const tcfConfigOptions = useMemo(
    () =>
      tcfConfigs?.items.map((config) => ({
        label: config.name,
        value: config.id,
      })) ?? [],
    [tcfConfigs],
  );

  const buttonPanel = (
    <div className="flex justify-between border-t border-[#DEE5EE] p-4">
      <Button onClick={() => router.push(PRIVACY_EXPERIENCE_ROUTE)}>
        Cancel
      </Button>
      <Button
        htmlType="submit"
        type="primary"
        data-testid="save-btn"
        disabled={isSubmitting || !dirty || !isValid}
        loading={isSubmitting}
      >
        Save
      </Button>
    </div>
  );

  return (
    <PrivacyExperienceConfigColumnLayout buttonPanel={buttonPanel}>
      <BackButton backPath={PRIVACY_EXPERIENCE_ROUTE} mt={4} />
      <Heading fontSize="md" fontWeight="semibold">
        Configure experience
      </Heading>
      <CustomTextInput
        name="name"
        id="name"
        label="Name (internal admin use only)"
        isRequired
        variant="stacked"
      />
      {values.component !== ComponentType.TCF_OVERLAY && (
        <ControlledSelect
          name="component"
          id="component"
          options={componentTypeOptions}
          label="Experience type"
          layout="stacked"
          disabled={!!initialValues.component}
          isRequired
        />
      )}
      <Collapse
        in={values.component === ComponentType.TCF_OVERLAY}
        animateOpacity
      >
        {values.component === ComponentType.TCF_OVERLAY && (
          <Tooltip
            title={
              // eslint-disable-next-line no-nested-ternary
              !appConfig?.consent?.override_vendor_purposes
                ? "You must enable the Override vendor purposes setting in consent settings to select a TCF configuration."
                : !tcfConfigOptions?.length
                  ? "No TCF configurations found. Please create a TCF configuration in 'Consent settings' to select one."
                  : undefined
            }
          >
            <div>
              <ControlledSelect
                name="tcf_configuration_id"
                id="tcf_configuration_id"
                label="TCF Configuration"
                options={tcfConfigOptions}
                layout="stacked"
                disabled={
                  !tcfConfigOptions?.length ||
                  !appConfig?.consent?.override_vendor_purposes
                }
                tooltip='Select a TCF configuration. Configurations are defined in "Consent settings" and apply to TCF privacy experiences.'
                allowClear
              />
            </div>
          </Tooltip>
        )}
      </Collapse>
      <Collapse
        in={values.component === ComponentType.TCF_OVERLAY}
        animateOpacity
      >
        {values.component === ComponentType.TCF_OVERLAY && (
          <ControlledSelect
            name="reject_all_mechanism"
            id="reject_all_mechanism"
            options={tcfRejectAllMechanismOptions}
            defaultValue={RejectAllMechanism.REJECT_ALL}
            label="Reject all behavior"
            layout="stacked"
            tooltip="Reject All: Blocks both consent and legitimate interest data processing across all purposes, features, and vendors. Reject Consent-Only: Blocks only consent-based processing, but allows legitimate interest processing to continue, requiring separate objection."
          />
        )}
      </Collapse>
      <Collapse
        in={
          values.component === ComponentType.BANNER_AND_MODAL ||
          values.component === ComponentType.TCF_OVERLAY
        }
        animateOpacity
      >
        {(values.component === ComponentType.BANNER_AND_MODAL ||
          values.component === ComponentType.TCF_OVERLAY) && (
          <ControlledSelect
            name="layer1_button_options"
            id="layer1_button_options"
            defaultValue={Layer1ButtonOption.OPT_IN_OPT_OUT}
            options={
              values.component === ComponentType.TCF_OVERLAY
                ? tcfBannerButtonOptions
                : bannerButtonOptions
            }
            label={
              values.component === ComponentType.TCF_OVERLAY
                ? "Reject all visibility"
                : "Banner options"
            }
            layout="stacked"
          />
        )}
      </Collapse>
      <Collapse
        in={
          values.component !== ComponentType.PRIVACY_CENTER &&
          values.component !== ComponentType.HEADLESS
        }
        animateOpacity
      >
        <Box p="1px">
          <CustomSwitch
            name="dismissable"
            id="dismissable"
            label="Allow user to dismiss"
            variant="stacked"
          />
        </Box>
      </Collapse>
      <Divider />
      <Heading fontSize="md" fontWeight="semibold">
        Privacy notices
      </Heading>
      {values.component === ComponentType.TCF_OVERLAY ? (
        <ScrollableList<string>
          addButtonLabel="Add privacy notice"
          allItems={allPrivacyNoticesWithTcfPlaceholder.map((n) => n.id)}
          values={privacyNoticeIdsWithTcfId(values)}
          setValues={(newValues) =>
            setFieldValue("privacy_notice_ids", newValues)
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
          getItemLabel={getPrivacyNoticeName}
          draggable
          baseTestId="privacy-notice"
        />
      ) : (
        <ScrollableList<string>
          addButtonLabel="Add privacy notice"
          allItems={filterNoticesForOnlyParentNotices(allPrivacyNotices).map(
            (n) => n.id,
          )}
          values={values.privacy_notice_ids ?? []}
          setValues={(newValues) =>
            setFieldValue("privacy_notice_ids", newValues)
          }
          getItemLabel={getPrivacyNoticeName}
          draggable
          baseTestId="privacy-notice"
        />
      )}
      <Collapse
        in={
          values.component === ComponentType.BANNER_AND_MODAL &&
          !!values.privacy_notice_ids?.length
        }
        animateOpacity
      >
        {values.component === ComponentType.BANNER_AND_MODAL && (
          <Box p="1px">
            <CustomSwitch
              name="show_layer1_notices"
              id="show_layer1_notices"
              label="Add privacy notices to banner"
              variant="stacked"
            />
          </Box>
        )}
      </Collapse>
      <Divider />
      <Text as="h2" fontWeight="600">
        Locations & Languages
      </Text>
      <ScrollableList
        label="Locations for this experience"
        addButtonLabel="Add location"
        allItems={allSelectedRegions}
        values={values.regions ?? []}
        setValues={(newValues) => setFieldValue("regions", newValues)}
        getItemLabel={(item) => PRIVACY_NOTICE_REGION_RECORD[item]}
        draggable
        baseTestId="location"
      />
      {translationsEnabled ? (
        <>
          <ScrollableList
            label="Languages for this experience"
            addButtonLabel="Add language"
            values={values.translations ?? []}
            setValues={(newValues) => setFieldValue("translations", newValues)}
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
            onRowClick={onSelectTranslation}
            selectOnAdd
            draggable
            baseTestId="language"
          />
          <CustomSwitch
            name="auto_detect_language"
            id="auto_detect_language"
            label="Auto detect language"
            variant="stacked"
          />
        </>
      ) : (
        <Button
          icon={<ArrowForwardIcon />}
          iconPosition="end"
          onClick={() => onSelectTranslation(values.translations![0])}
          data-testid="edit-experience-btn"
        >
          Edit experience text
        </Button>
      )}
      <Divider />
      <Heading fontSize="md" fontWeight="semibold">
        Properties
      </Heading>
      <ScrollableList
        label="Associated properties"
        addButtonLabel="Add property"
        idField="id"
        nameField="name"
        allItems={allProperties.map((property: Property) => ({
          id: property.id,
          name: property.name,
        }))}
        values={values.properties ?? []}
        setValues={(newValues) => setFieldValue("properties", newValues)}
        draggable
        maxHeight={100}
        baseTestId="property"
      />
      <Divider />
      <CustomSwitch
        name="auto_subdomain_cookie_deletion"
        id="auto_subdomain_cookie_deletion"
        label="Automatically delete subdomain cookies"
        variant="stacked"
        tooltip="If enabled, automatically deletes cookies set on subdomains in addition to main domain where appropriate. Recommended to enable for full consent compliance."
      />
    </PrivacyExperienceConfigColumnLayout>
  );
};
export default PrivacyExperienceForm;
