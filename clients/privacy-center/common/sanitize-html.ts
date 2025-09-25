import sanitize from "sanitize-html";

export default function sanitizeHTML(input: string) {
  return sanitize(input, {
    allowedTags: [
      "a",
      "blockquote",
      "br",
      "div",
      "em",
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "i",
      "li",
      "ol",
      "ul",
      "p",
      "pre",
      "q",
      "rt",
      "ruby",
      "s",
      "span",
      "strong",
      "u",
    ],
    allowedAttributes: {
      a: ["href", "hreflang", "target"],
    },
  });
}
