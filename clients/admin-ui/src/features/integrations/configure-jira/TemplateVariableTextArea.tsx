import { Input, Typography } from "fidesui";
import { KeyboardEvent, useRef, useState } from "react";

import styles from "./TemplateVariableTextArea.module.scss";

interface TemplateVariable {
  name: string;
  description: string;
  example_value?: string;
}

interface TemplateVariableTextAreaProps {
  value?: string;
  onChange?: (value: string) => void;
  variables: TemplateVariable[];
  rows?: number;
  placeholder?: string;
}

const TemplateVariableTextArea = ({
  value = "",
  onChange,
  variables,
  rows = 4,
  placeholder,
}: TemplateVariableTextAreaProps) => {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<number>(0);

  // Index of the `{{` that triggered the dropdown, or null if not open
  const [triggerIndex, setTriggerIndex] = useState<number | null>(null);
  const [filterText, setFilterText] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const listboxRef = useRef<HTMLDivElement>(null);

  const scrollOptionIntoView = (index: number) => {
    const options = listboxRef.current?.querySelectorAll("[role='option']");
    (options?.[index] as HTMLElement | undefined)?.scrollIntoView({
      block: "nearest",
    });
  };

  const getTextarea = (): HTMLTextAreaElement | null =>
    wrapperRef.current?.querySelector("textarea") ?? null;

  const filteredVars =
    triggerIndex !== null
      ? variables.filter((v) =>
          v.name.toLowerCase().startsWith(filterText.toLowerCase()),
        )
      : [];

  const closeDropdown = () => setTriggerIndex(null);

  const selectVariable = (varName: string) => {
    const cursor = cursorRef.current;
    if (triggerIndex === null) {
      return;
    }

    const before = value.slice(0, triggerIndex);
    const after = value.slice(cursor);
    const insertion = `{{ ${varName} }}`;
    const newValue = `${before}${insertion}${after}`;
    const newCursor = triggerIndex + insertion.length;

    onChange?.(newValue);
    closeDropdown();

    setTimeout(() => {
      const textarea = getTextarea();
      if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(newCursor, newCursor);
      }
    }, 0);
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    const cursor = e.target.selectionStart ?? text.length;
    cursorRef.current = cursor;

    // Look for an unclosed `{{` before the cursor
    const beforeCursor = text.slice(0, cursor);
    const triggerPos = beforeCursor.lastIndexOf("{{");

    if (triggerPos !== -1) {
      const afterTrigger = beforeCursor.slice(triggerPos + 2);
      if (!afterTrigger.includes("}}")) {
        setTriggerIndex(triggerPos);
        setFilterText(afterTrigger.trimStart());
        setActiveIndex(0);
        onChange?.(text);
        return;
      }
    }

    closeDropdown();
    onChange?.(text);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (triggerIndex === null || filteredVars.length === 0) {
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = Math.min(activeIndex + 1, filteredVars.length - 1);
      setActiveIndex(next);
      scrollOptionIntoView(next);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = Math.max(activeIndex - 1, 0);
      setActiveIndex(prev);
      scrollOptionIntoView(prev);
    } else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      if (filteredVars[activeIndex]) {
        selectVariable(filteredVars[activeIndex].name);
      }
    } else if (e.key === "Escape") {
      closeDropdown();
    }
  };

  const handleKeyUp = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    cursorRef.current =
      (e.target as HTMLTextAreaElement).selectionStart ?? cursorRef.current;
  };

  const handleClick = (e: React.MouseEvent<HTMLTextAreaElement>) => {
    cursorRef.current =
      (e.target as HTMLTextAreaElement).selectionStart ?? cursorRef.current;
  };

  return (
    <div ref={wrapperRef} className="relative">
      <Input.TextArea
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onKeyUp={handleKeyUp}
        onClick={handleClick}
        onBlur={() => setTimeout(closeDropdown, 150)}
        rows={rows}
        placeholder={placeholder}
      />
      {triggerIndex !== null && filteredVars.length > 0 && (
        <div
          ref={listboxRef}
          role="listbox"
          className={`absolute inset-x-0 top-full z-[1000] max-h-[220px] overflow-y-auto ${styles.dropdown}`}
        >
          {filteredVars.map((v, i) => (
            <div
              key={v.name}
              role="option"
              aria-selected={i === activeIndex}
              tabIndex={-1}
              // preventDefault keeps textarea focused so blur doesn't fire
              onMouseDown={(e) => {
                e.preventDefault();
                selectVariable(v.name);
              }}
              onMouseEnter={() => setActiveIndex(i)}
              className={`flex cursor-pointer items-baseline gap-2 px-3 py-[7px] ${styles.option} ${i === activeIndex ? styles.optionActive : ""}`}
            >
              <Typography.Text code>{`{{ ${v.name} }}`}</Typography.Text>
              {v.description && (
                <Typography.Text type="secondary" className="text-xs">
                  {v.description}
                </Typography.Text>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TemplateVariableTextArea;
