import {
  ArrowForwardIcon,
  Button,
  ButtonGroup,
  Divider,
  Flex,
  Heading,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";
import { useRouter } from "next/router";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import ScrollableList from "~/features/common/ScrollableList";
import { selectAllLanguages } from "~/features/privacy-experience/language.slice";
import {
  selectAllPrivacyNotices,
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
  PrivacyNoticeRegion,
  SupportedLanguage,
} from "~/types/api";

const componentTypeOptions = [
  {
    label: "Banner and modal",
    value: ComponentType.BANNER_AND_MODAL,
  },
  {
    label: "Banner",
    value: ComponentType.MODAL,
  },
];

export const PrivacyExperienceTranslationForm = ({
  name,
}: {
  name: string;
}) => (
  <Flex direction="column" gap={4} w="full">
    <Text>Editing the {name} translation...</Text>
  </Flex>
);

const PrivacyExperienceForm = ({
  onSelectTranslation,
}: {
  onSelectTranslation: (t: ExperienceTranslation) => void;
}) => {
  const router = useRouter();

  const [editingStyle, setEditingStyle] = useState<boolean>(false);
  const { values, setFieldValue, dirty, isValid, isSubmitting } =
    useFormikContext<ExperienceConfigCreate>();

  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });
  const allPrivacyNotices = useAppSelector(selectAllPrivacyNotices);

  const getPrivacyNoticeName = (id: string) => {
    const notice = allPrivacyNotices.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  const allRegions = Object.entries(PrivacyNoticeRegion).map(
    (entry) => entry[1]
  ) as PrivacyNoticeRegion[];

  const allLanguages = useAppSelector(selectAllLanguages);

  const getTranslationDisplayName = (t: ExperienceTranslation) => {
    const language = allLanguages.find((lang) => lang.id === t.language);
    const name = language ? language.name : t.language;
    return `${name}${t.is_default ? " (Default)" : ""}`;
  };

  if (editingStyle) {
    return (
      <>
        <Button onClick={() => setEditingStyle(false)}>
          Back to main form
        </Button>
        <Text>Editing experience style coming soon™</Text>
      </>
    );
  }

  return (
    <Flex
      direction="column"
      minH="full"
      w="25%"
      borderRight="1px solid #DEE5EE"
    >
      <Flex direction="column" h="full" overflow="scroll" px={4}>
        <Flex direction="column" gap={4} w="full">
          {" "}
          <BackButton backPath={PRIVACY_EXPERIENCE_ROUTE} mt={4} />
          <Heading fontSize="md" fontWeight="semibold">
            Configure experience
          </Heading>
          <CustomTextInput
            name="name"
            id="name"
            label="Name (internal admin use only)"
            variant="stacked"
          />
          <CustomSelect
            name="component"
            id="component"
            options={componentTypeOptions}
            label="Experience Type"
            variant="stacked"
            isRequired
          />
          <CustomSwitch
            name="dismissable"
            id="dismissable"
            label="Overlay is dismissable"
            variant="stacked"
          />
          <Button
            onClick={() => setEditingStyle(true)}
            size="sm"
            variant="outline"
            rightIcon={<ArrowForwardIcon />}
          >
            Customize appearance
          </Button>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold">
            Privacy notices
          </Heading>
          <ScrollableList
            addButtonLabel="Add privacy notice"
            allItems={allPrivacyNotices.map((n) => n.id)}
            values={values.privacy_notice_ids ?? []}
            setValues={(newValues) =>
              setFieldValue("privacy_notice_ids", newValues)
            }
            getItemLabel={getPrivacyNoticeName}
            draggable
          />
          <Divider />
          <Text as="h2" fontWeight="600">
            Locations & Languages
          </Text>
          <ScrollableList
            label="Locations for this experience"
            addButtonLabel="Add location"
            allItems={allRegions}
            values={values.regions ?? []}
            setValues={(newValues) => setFieldValue("regions", newValues)}
            getItemLabel={(item) => PRIVACY_NOTICE_REGION_RECORD[item]}
            draggable
          />
          <ScrollableList
            label="Languages for this experience"
            addButtonLabel="Add language"
            values={values.translations ?? []}
            setValues={(newValues) => setFieldValue("translations", newValues)}
            idField="language"
            canDeleteItem={(item) => !item.is_default}
            allItems={allLanguages.map((lang) => ({
              language: lang.id as SupportedLanguage,
              is_default: false,
            }))}
            getItemLabel={getTranslationDisplayName}
            createNewValue={(opt) => ({
              language: opt.value as SupportedLanguage,
              is_default: false,
            })}
            onRowClick={onSelectTranslation}
            selectOnAdd
            draggable
          />
        </Flex>
      </Flex>
      <ButtonGroup size="sm" borderTop="1px solid #DEE5EE" p={4}>
        <Button
          variant="outline"
          onClick={() => router.push(PRIVACY_EXPERIENCE_ROUTE)}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          colorScheme="primary"
          data-testid="save-btn"
          isDisabled={isSubmitting || !dirty || !isValid}
          isLoading={isSubmitting}
        >
          Save
        </Button>
      </ButtonGroup>
    </Flex>
  );
};

export default PrivacyExperienceForm;
