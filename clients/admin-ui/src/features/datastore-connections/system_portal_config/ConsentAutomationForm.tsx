import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  ArrowDownRightIcon,
  Box,
  BoxProps,
  Button,
  FormLabel,
  HStack,
  SimpleGrid,
  Skeleton,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik, FormikValues } from "formik";
import { Fragment, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { Option, SelectInput } from "~/features/common/form/inputs";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useGetConsentableItemsQuery,
  useUpdateConsentableItemsMutation,
} from "~/features/plus/plus.slice";
import {
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import { ConsentableItem } from "~/types/api/models/ConsentableItem";
import { isErrorResult } from "~/types/errors";

interface ConsentableItemFieldProps {
  item: ConsentableItem;
  options: Option[];
  onNoticeChange: (newValue: ConsentableItem) => void;
  isChild?: boolean;
}

const ConsentableItemField = ({
  item,
  options = [],
  onNoticeChange,
  isChild,
}: ConsentableItemFieldProps) => {
  const { external_id: id, name } = item;
  const fieldName = `${id}-notice_id`;
  return (
    <>
      <HStack flexGrow={1}>
        {isChild && <ArrowDownRightIcon />}
        <FormLabel
          id={`${id}-label`}
          data-testid={`consentable-item-label${isChild ? "-child" : ""}`}
          m={0}
          fontSize="14px"
          fontWeight={isChild ? "normal" : "semibold"}
        >
          {name}
        </FormLabel>
      </HStack>
      <Box data-testid="consentable-item-select">
        <SelectInput
          placeholder="None"
          size="sm"
          fieldName={fieldName}
          options={options}
          ariaLabel="Notices"
          ariaDescribedby={`${id}-label`}
          isClearable
          onChange={(option: Option | undefined) => {
            const value = option?.value;
            // eslint-disable-next-line no-param-reassign
            item = { ...item, notice_id: value };
            onNoticeChange(item);
          }}
        />
      </Box>
    </>
  );
};

interface ConsentAutomationFormProps extends BoxProps {
  connectionKey: string;
}

export const ConsentAutomationForm = ({
  connectionKey,
  ...props
}: ConsentAutomationFormProps) => {
  const toast = useToast();

  const { data, isLoading: isLoadingConsentableItems } =
    useGetConsentableItemsQuery(connectionKey);
  const [consentableItemsMutationTrigger] = useUpdateConsentableItemsMutation();

  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  const { data: notices, isLoading: isLoadingNotices } =
    useGetAllPrivacyNoticesQuery({
      page: noticePage,
      size: noticePageSize,
    });

  const [consentableItems, setConsentableItems] = useState<ConsentableItem[]>();
  const [noticesOptions, setNoticesOptions] = useState<Option[]>([]);
  const initialValues = useMemo(() => {
    return consentableItems?.reduce(
      (acc, item) => {
        if (item.notice_id) {
          // eslint-disable-next-line no-param-reassign
          acc[`${item.external_id}-notice_id`] = item.notice_id;
        }
        if (item.children?.length) {
          item.children.forEach((child) => {
            if (child.notice_id) {
              // eslint-disable-next-line no-param-reassign
              acc[`${child.external_id}-notice_id`] = child.notice_id;
            }
          });
        }
        return acc;
      },
      {} as FormikValues & Record<string, string>,
    );
  }, [consentableItems]);

  const handleSubmit = async () => {
    const result = await consentableItemsMutationTrigger({
      connectionKey,
      consentableItems: consentableItems as ConsentableItem[],
    });

    if (isErrorResult(result)) {
      toast(errorToastParams("Failed to save consent automation"));
    } else {
      toast(successToastParams(`Consent automation has been saved`));
    }
  };

  useEffect(() => {
    if (data) {
      setConsentableItems(data);
    }
  }, [data]);

  useEffect(() => {
    if (notices) {
      setNoticesOptions(
        notices.items.map((notice) => ({
          label: notice.name,
          value: notice.id,
        })),
      );
    }
  }, [notices]);

  if (isLoadingConsentableItems || isLoadingNotices) {
    return (
      <Box borderWidth="1px" borderRadius="md" {...props}>
        <Skeleton height="35px" />
      </Box>
    );
  }

  if (!consentableItems || !notices) {
    return null;
  }

  const handleNoticeChange = (
    value: ConsentableItem,
    parent?: ConsentableItem,
  ): void => {
    const updatedItems = consentableItems.map((i) => {
      if (
        parent
          ? i.external_id === parent.external_id
          : i.external_id === value.external_id
      ) {
        if (parent) {
          return {
            ...i,
            children: i.children?.map((child) => {
              if (child.external_id === value.external_id) {
                return value;
              }
              return child;
            }),
          };
        }
        return value;
      }
      return i;
    });
    setConsentableItems(updatedItems);
  };

  return (
    <Box borderWidth="1px" borderRadius="md" {...props}>
      <Accordion allowMultiple data-testid="accordion-consent-automation">
        <AccordionItem border="none">
          <AccordionButton>
            <Box as="span" flex="1" textAlign="left">
              <Text as="h2" fontWeight="semibold" fontSize="sm">
                Consent automation
              </Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel
            p={5}
            fontSize="sm"
            data-testid="accordion-panel-consent-automation"
          >
            <Text mb={7}>
              Configure the notices that will trigger consent propagation for
              this integration. A default value can be used to trigger every
              consent preference or each item can be configured individually.
            </Text>
            <Formik initialValues={initialValues || {}} onSubmit={handleSubmit}>
              <Form>
                <SimpleGrid columns={2} spacing={3}>
                  {consentableItems.map((item) => (
                    <Fragment key={item.external_id}>
                      <ConsentableItemField
                        item={item}
                        options={noticesOptions}
                        onNoticeChange={handleNoticeChange}
                      />
                      {item.children?.map((child) => (
                        <ConsentableItemField
                          item={child}
                          options={noticesOptions}
                          key={child.external_id}
                          isChild
                          onNoticeChange={(newValue) =>
                            handleNoticeChange(newValue, item)
                          }
                        />
                      ))}
                    </Fragment>
                  ))}
                </SimpleGrid>
                <HStack justifyContent="flex-end" mt={3}>
                  <Button
                    bg="primary.800"
                    color="white"
                    size="sm"
                    variant="solid"
                    type="submit"
                    _active={{ bg: "primary.500" }}
                    _hover={{ bg: "primary.400" }}
                    data-testid="save-consent-automation"
                  >
                    Save
                  </Button>
                </HStack>
              </Form>
            </Formik>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </Box>
  );
};
