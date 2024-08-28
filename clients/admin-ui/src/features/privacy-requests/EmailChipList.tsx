import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  forwardRef,
  Input,
  Tag,
  TagCloseButton,
  TagLabel,
  VStack,
  Wrap,
} from "fidesui";
import { FieldArrayRenderProps } from "formik";
import React, { useState } from "react";

const EMAIL_REGEXP = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
const isValidEmail = (email: string) => EMAIL_REGEXP.test(email);

type EmailChipListProps = {
  isRequired: boolean;
};

const EmailChipList = forwardRef(
  (
    {
      isRequired = false,
      ...props
    }: FieldArrayRenderProps & EmailChipListProps,
    ref,
  ) => {
    const { emails }: { emails: string[] } = props.form.values;
    const [inputValue, setInputValue] = useState("");

    const emailChipExists = (email: string) => emails.includes(email);

    const addEmails = (emailsToAdd: string[]) => {
      const validatedEmails = emailsToAdd
        .map((e) => e.trim())
        .filter((email) => isValidEmail(email) && !emailChipExists(email));
      validatedEmails.forEach((email) => props.push(email));
      setInputValue("");
    };

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(event.target.value);
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (["Enter", "Tab", ","].includes(event.key)) {
        event.preventDefault();
        addEmails([inputValue]);
      }
    };

    const handlePaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
      event.preventDefault();
      const pastedData = event.clipboardData.getData("text");
      const pastedEmails = pastedData.split(",");
      addEmails(pastedEmails);
    };

    return (
      <FormControl
        alignItems="baseline"
        display="inline-flex"
        isInvalid={!!props.form.errors[props.name]}
        isRequired={isRequired}
      >
        <FormLabel fontSize="md" htmlFor="email">
          Email
        </FormLabel>
        <VStack align="flex-start" w="inherit">
          {/* @ts-ignore */}
          <Input
            autoComplete="off"
            placeholder="Type or paste email addresses separated by commas and press `Enter` or `Tab`..."
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            ref={ref}
            size="sm"
            type="email"
            value={inputValue}
          />
          <FormErrorMessage>
            {props.form.errors[props.name] as string}
          </FormErrorMessage>
          {emails.length > 0 && (
            <Wrap spacing={1} mb={3} pt="8px">
              {emails.map((email, index) => (
                <Tag
                  key={email}
                  borderRadius="full"
                  backgroundColor="primary.400"
                  color="white"
                  size="sm"
                  variant="solid"
                >
                  <TagLabel>{email}</TagLabel>
                  <TagCloseButton
                    onClick={() => {
                      props.remove(index);
                    }}
                  />
                </Tag>
              ))}
            </Wrap>
          )}
        </VStack>
      </FormControl>
    );
  },
);

export default EmailChipList;
