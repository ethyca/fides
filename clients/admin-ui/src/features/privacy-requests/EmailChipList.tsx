import { Input, Tag } from "fidesui";
import React, { forwardRef, useState } from "react";

const EMAIL_REGEXP = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
const isValidEmail = (email: string) => EMAIL_REGEXP.test(email);

type EmailChipListProps = {
  emails: string[];
  onEmailsChange: (emails: string[]) => void;
  disabled?: boolean;
};

const EmailChipList = forwardRef<HTMLInputElement, EmailChipListProps>(
  ({ emails, onEmailsChange, disabled = false }, ref) => {
    const [inputValue, setInputValue] = useState("");

    const emailChipExists = (email: string) => emails.includes(email);

    const addEmails = (emailsToAdd: string[]) => {
      if (disabled) return;
      const validatedEmails = emailsToAdd
        .map((e) => e.trim())
        .filter((email) => isValidEmail(email) && !emailChipExists(email));
      if (validatedEmails.length > 0) {
        onEmailsChange([...emails, ...validatedEmails]);
        setInputValue("");
      }
    };

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (disabled) return;
      setInputValue(event.target.value);
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (disabled) return;
      if (["Enter", "Tab", ","].includes(event.key)) {
        event.preventDefault();
        addEmails([inputValue]);
      }
    };

    const handlePaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
      if (disabled) return;
      event.preventDefault();
      const pastedData = event.clipboardData.getData("text");
      const pastedEmails = pastedData.split(",");
      addEmails(pastedEmails);
    };

    const removeEmail = (emailToRemove: string) => {
      if (disabled) return;
      onEmailsChange(emails.filter((email) => email !== emailToRemove));
    };

    return (
      <div className="w-full">
        <Input
          autoComplete="off"
          placeholder="Enter one or more email addresses"
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          ref={ref}
          type="email"
          value={inputValue}
          disabled={disabled}
        />
        {emails.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {emails.map((email) => (
              <Tag
                key={email}
                closable={!disabled}
                onClose={() => removeEmail(email)}
                color="default"
              >
                {email}
              </Tag>
            ))}
          </div>
        )}
      </div>
    );
  },
);

EmailChipList.displayName = "EmailChipList";

export default EmailChipList;
