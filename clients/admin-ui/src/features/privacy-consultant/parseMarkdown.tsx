import React from "react";

/**
 * Simple markdown parser that supports basic formatting:
 * - **bold** or __bold__
 * - *italic* or _italic_
 * - `code`
 *
 * Falls back to plain text if parsing fails.
 */
export const parseMarkdown = (text: string): React.ReactNode => {
  try {
    // Split by line breaks first to preserve them
    const lines = text.split("\n");

    return lines.map((line, lineIndex) => {
      const elements: React.ReactNode[] = [];
      let remaining = line;
      let keyIndex = 0;

      // Process inline formatting
      while (remaining.length > 0) {
        // Match **bold** or __bold__
        const boldMatch = remaining.match(/^(.*?)(\*\*|__)(.+?)\2(.*)$/s);
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
        const italicMatch = remaining.match(/^(.*?)(\*|_)(.+?)\2(.*)$/s);
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
        const codeMatch = remaining.match(/^(.*?)`(.+?)`(.*)$/s);
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
    // Fallback to plain text if parsing fails
    return text;
  }
};
