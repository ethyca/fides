import { antTheme, Input, Typography } from "fidesui";
import { KeyboardEvent, useRef, useState } from "react";

interface TemplateVariable {
  name: string;
  description: string;
  example_value?: string;
}

interface TemplateVariableTextAreaProps
  extends Omit<
    React.ComponentPropsWithoutRef<typeof Input.TextArea>,
    "onChange" | "value"
  > {
  variables: TemplateVariable[];
  onChange?: (value: string) => void;
  value?: string;
}

const TemplateVariableTextArea = ({
  value = "",
  onChange,
  variables,
  rows = 4,
  placeholder,
  ...props
}: TemplateVariableTextAreaProps) => {
  const { token } = antTheme.useToken();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<number>(0);

  // Index of the `__` that triggered the dropdown, or null if not open
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
    const insertion = `__${varName.toUpperCase()}__`;
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

    const beforeCursor = text.slice(0, cursor);

    // Find the most recent trigger (`/` or `__`) before the cursor and check
    // whether the text typed after it is still a valid partial variable name.
    // Only match `/` when it immediately precedes the current word (no
    // intervening alphanumeric text), to avoid false positives on prose like
    // "access/erasure" where the cursor happens to be in "erasure".
    const slashPos = /\/([A-Za-z_]*)$/.exec(beforeCursor);
    const doubleUnderscorePos = /__([A-Za-z_]*)$/.exec(beforeCursor);

    const candidates: { pos: number; len: number }[] = [
      ...(slashPos ? [{ pos: slashPos.index, len: 1 }] : []),
      ...(doubleUnderscorePos
        ? [{ pos: doubleUnderscorePos.index, len: 2 }]
        : []),
    ];

    const match = candidates
      .sort((a, b) => b.pos - a.pos)
      .find(({ pos, len }) => {
        const afterTrigger = beforeCursor.slice(pos + len);
        return /^[A-Za-z_]*$/.test(afterTrigger);
      });

    if (match) {
      const afterTrigger = beforeCursor.slice(match.pos + match.len);
      setTriggerIndex(match.pos);
      setFilterText(afterTrigger.toUpperCase());
      setActiveIndex(0);
      onChange?.(text);
      return;
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
        {...props}
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
          className="absolute inset-x-0 top-full z-[1000] max-h-[220px] overflow-y-auto"
          style={{
            background: token.colorBgContainer,
            border: `1px solid ${token.colorBorder}`,
            borderRadius: token.borderRadiusLG,
            boxShadow: token.boxShadowSecondary,
          }}
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
              className="flex cursor-pointer items-baseline gap-2 px-3 py-[7px]"
              style={{
                background:
                  i === activeIndex
                    ? token.colorFillAlter
                    : token.colorBgContainer,
                borderBottom:
                  i < filteredVars.length - 1
                    ? `1px solid ${token.colorBorderSecondary}`
                    : undefined,
              }}
            >
              <Typography.Text
                code
              >{`__${v.name.toUpperCase()}__`}</Typography.Text>
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
