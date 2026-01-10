import { Input, Tag } from "fidesui";
import React, { forwardRef, useState } from "react";

const EMAIL_REGEXP = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
const isValidEmail = (email: string) => EMAIL_REGEXP.test(email);

type EmailChipListProps = {
  emails: string[];
  onEmailsChange: (emails: string[]) => void;
};

const EmailChipList = forwardRef<HTMLInputElement, EmailChipListProps>(
  ({ emails, onEmailsChange }, ref) => {
    const [inputValue, setInputValue] = useState("");

    const emailChipExists = (email: string) => emails.includes(email);

    const addEmails = (emailsToAdd: string[]) => {
      const validatedEmails = emailsToAdd
        .map((e) => e.trim())
        .filter((email) => isValidEmail(email) && !emailChipExists(email));
      if (validatedEmails.length > 0) {
        onEmailsChange([...emails, ...validatedEmails]);
        setInputValue("");
      }
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

    const removeEmail = (emailToRemove: string) => {
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
        />
        {emails.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {emails.map((email) => (
              <Tag
                key={email}
                closable
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
