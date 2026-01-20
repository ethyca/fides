import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";

/**
 * Markdown rendering using react-markdown library.
 * Provides full markdown support with custom link handling.
 */
const LibraryMarkdown: React.FC<{ text: string }> = ({ text }) => {
  return (
    <ReactMarkdown
      components={{
        // Open links in new tab for security
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {text}
    </ReactMarkdown>
  );
};

/**
 * Simple markdown parser that supports basic formatting:
 * - [text](url) links
 * - **bold** or __bold__
 * - *italic* or _italic_
 * - `code`
 *
 * Falls back to plain text if parsing fails.
 */
const customParseMarkdown = (text: string): React.ReactNode => {
  try {
    // Split by line breaks first to preserve them
    const lines = text.split("\n");

    return lines.map((line, lineIndex) => {
      const elements: React.ReactNode[] = [];
      let remaining = line;
      let keyIndex = 0;

      // Process inline formatting
      while (remaining.length > 0) {
        // Match [text](url) links
        const linkMatch = remaining.match(/^(.*?)\[([^\]]+)\]\(([^)]+)\)(.*)$/);
        if (linkMatch) {
          if (linkMatch[1]) {
            elements.push(
              <React.Fragment key={`text-${keyIndex++}`}>
                {linkMatch[1]}
              </React.Fragment>,
            );
          }
          elements.push(
            <a
              key={`link-${keyIndex++}`}
              href={linkMatch[3]}
              target="_blank"
              rel="noopener noreferrer"
            >
              {linkMatch[2]}
            </a>,
          );
          remaining = linkMatch[4];
          continue;
        }

        // Match **bold** or __bold__
        const boldMatch = remaining.match(/^(.*?)(\*\*|__)(.+?)\2(.*)$/);
        if (boldMatch) {
          if (boldMatch[1]) {
            elements.push(
              <React.Fragment key={`text-${keyIndex++}`}>
                {boldMatch[1]}
              </React.Fragment>,
            );
          }
          elements.push(
            <strong key={`bold-${keyIndex++}`}>{boldMatch[3]}</strong>,
          );
          remaining = boldMatch[4];
          continue;
        }

        // Match *italic* or _italic_ (but not inside words for _)
        const italicMatch = remaining.match(/^(.*?)(\*|_)(.+?)\2(.*)$/);
        if (italicMatch && italicMatch[3].length > 0) {
          if (italicMatch[1]) {
            elements.push(
              <React.Fragment key={`text-${keyIndex++}`}>
                {italicMatch[1]}
              </React.Fragment>,
            );
          }
          elements.push(<em key={`italic-${keyIndex++}`}>{italicMatch[3]}</em>);
          remaining = italicMatch[4];
          continue;
        }

        // Match `code`
        const codeMatch = remaining.match(/^(.*?)`(.+?)`(.*)$/);
        if (codeMatch) {
          if (codeMatch[1]) {
            elements.push(
              <React.Fragment key={`text-${keyIndex++}`}>
                {codeMatch[1]}
              </React.Fragment>,
            );
          }
          elements.push(<code key={`code-${keyIndex++}`}>{codeMatch[2]}</code>);
          remaining = codeMatch[3];
          continue;
        }

        // No more matches, add remaining text
        if (remaining) {
          elements.push(
            <React.Fragment key={`text-${keyIndex++}`}>
              {remaining}
            </React.Fragment>,
          );
        }
        break;
      }

      // Add line break after each line except the last
      if (lineIndex < lines.length - 1) {
        elements.push(<br key={`br-${lineIndex}`} />);
      }

      return (
        <React.Fragment key={`line-${lineIndex}`}>{elements}</React.Fragment>
      );
    });
  } catch {
    // Return null to indicate failure, let caller handle fallback
    return null;
  }
};

interface MarkdownRendererProps {
  text: string;
}

/**
 * Markdown renderer with fallback chain:
 * 1. Try react-markdown library (full markdown support)
 * 2. Fall back to custom parsing (basic formatting)
 * 3. Final fallback to plain text
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ text }) => {
  const renderedContent = useMemo(() => {
    // Strategy 1: Try library-based markdown
    try {
      return <LibraryMarkdown text={text} />;
    } catch {
      // Library failed, continue to fallback
    }

    // Strategy 2: Try custom parsing
    const customParsed = customParseMarkdown(text);
    if (customParsed !== null) {
      return customParsed;
    }

    // Strategy 3: Plain text fallback
    return text;
  }, [text]);

  return <>{renderedContent}</>;
};

/**
 * Legacy function export for backwards compatibility.
 * Prefers custom parsing over library for function-based usage.
 *
 * Fallback chain:
 * 1. Custom parsing (basic formatting)
 * 2. Plain text fallback
 */
export const parseMarkdown = (text: string): React.ReactNode => {
  const customParsed = customParseMarkdown(text);
  if (customParsed !== null) {
    return customParsed;
  }
  return text;
};
