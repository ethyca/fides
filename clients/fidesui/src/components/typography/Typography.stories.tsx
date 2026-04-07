import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button, theme, Typography } from "antd/lib";

import { Typography as FidesTypography } from "../../index";

const { Title, Text } = Typography;

const SAMPLE = "The quick brown fox jumps over the lazy dog";
const fontSizes = [24, 20, 18, 16, 14, 12];

// -- Shared helpers --

const Typeset = ({
  fontFamily,
  fontWeight,
  borderColor,
  secondaryColor,
}: {
  fontFamily: string;
  fontWeight: number;
  borderColor: string;
  secondaryColor: string;
}) => (
  <div style={{ marginTop: 12 }}>
    {fontSizes.map((size) => (
      <div
        key={size}
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 16,
          padding: "8px 0",
          borderBottom: `1px solid ${borderColor}`,
        }}
      >
        <span
          style={{
            width: 40,
            flexShrink: 0,
            fontFamily: '"Basier Square Mono", monospace',
            fontSize: 12,
            color: secondaryColor,
          }}
        >
          {size}px
        </span>
        <span style={{ fontFamily, fontWeight, fontSize: size }}>{SAMPLE}</span>
      </div>
    ))}
  </div>
);

const BrandRow = ({
  label,
  font,
  letterSpacing,
  lineHeight,
  sample,
  borderColor,
  secondaryColor,
}: {
  label: string;
  font: string;
  letterSpacing: string;
  lineHeight: string;
  sample: React.ReactNode;
  borderColor: string;
  secondaryColor: string;
}) => (
  <div
    style={{
      display: "flex",
      gap: 48,
      paddingBottom: 32,
      borderBottom: `1px dashed ${borderColor}`,
    }}
  >
    <div style={{ width: 220, flexShrink: 0 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{label}</div>
      <div
        style={{
          fontFamily: '"Basier Square Mono", monospace',
          fontSize: 13,
          lineHeight: 1.6,
          color: secondaryColor,
        }}
      >
        {font}
        <br />
        {letterSpacing} Letter Spacing
        <br />
        {lineHeight} Line Height
      </div>
    </div>
    <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
      {sample}
    </div>
  </div>
);

const ComponentRow = ({
  label,
  children,
  borderColor,
  secondaryColor,
}: {
  label: string;
  children: React.ReactNode;
  borderColor: string;
  secondaryColor: string;
}) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 24,
      padding: "8px 0",
      borderBottom: `1px solid ${borderColor}`,
    }}
  >
    <span
      style={{
        width: 140,
        flexShrink: 0,
        fontFamily: '"Basier Square Mono", monospace',
        fontSize: 12,
        color: secondaryColor,
      }}
    >
      {label}
    </span>
    <div style={{ flex: 1 }}>{children}</div>
  </div>
);

// -- Meta --

const meta = {
  title: "General/Typography",
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

// -- Stories --

const BrandGuidelinesStory = () => {
  const { token } = theme.useToken();
  const borderColor = token.colorBorderSecondary;
  const secondaryColor = token.colorTextDescription;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 48,
        maxWidth: 960,
      }}
    >
      <BrandRow
        label="Eyebrow Header"
        font="Basier Square, SemiBold"
        letterSpacing="10%"
        lineHeight="120%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Basier Square", sans-serif',
              fontWeight: 600,
              letterSpacing: "0.1em",
              lineHeight: 1.2,
              textTransform: "uppercase",
              fontSize: 14,
            }}
          >
            EYEBROW HEADER
          </span>
        }
      />
      <BrandRow
        label="Headline"
        font="Eliza, Medium"
        letterSpacing="-3%"
        lineHeight="110%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Eliza"',
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.1,
              fontSize: 64,
            }}
          >
            We use Eliza Medium for headlines
          </span>
        }
      />
      <BrandRow
        label="Subhead"
        font="Eliza, Medium"
        letterSpacing="-2%"
        lineHeight="110%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Eliza"',
              fontWeight: 500,
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              fontSize: 40,
            }}
          >
            Eliza Medium works well for subheads
          </span>
        }
      />
      <BrandRow
        label="Small Subhead"
        font="Basier Square, Medium"
        letterSpacing="-2%"
        lineHeight="120%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Basier Square", sans-serif',
              fontWeight: 500,
              letterSpacing: "-0.02em",
              lineHeight: 1.2,
              fontSize: 24,
            }}
          >
            As our sub-headers get smaller, we use Basier Square
          </span>
        }
      />
      <BrandRow
        label="Quote"
        font="Eliza, Medium Italic"
        letterSpacing="0%"
        lineHeight="120%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Eliza"',
              fontWeight: 500,
              fontStyle: "italic",
              lineHeight: 1.2,
              fontSize: 32,
            }}
          >
            &ldquo;Ethyca uses Eliza Medium Italic for quotes to add elegance
            and emphasis, ensuring key statements stand out and convey a
            personal touch.&rdquo;
          </span>
        }
      />
      <BrandRow
        label="Body"
        font="Basier Square, Regular"
        letterSpacing="0%"
        lineHeight="150%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Basier Square", sans-serif',
              fontWeight: 400,
              lineHeight: 1.5,
              fontSize: 16,
            }}
          >
            The body copy uses Basier Square, which is specifically chosen for
            its exceptional clarity and readability. This choice ensures that
            the messaging remains clear, concise, and easy to read,
            significantly enhancing the overall effectiveness of our
            communication.
          </span>
        }
      />
      <BrandRow
        label="Captions"
        font="Basier Square Mono, Regular"
        letterSpacing="-3%"
        lineHeight="150%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Basier Square Mono", monospace',
              fontWeight: 400,
              letterSpacing: "-0.03em",
              lineHeight: 1.5,
              fontSize: 14,
            }}
          >
            Captions use Basier Square Mono and should be short and clear,
            aligning with the visual content, enhancing readability, and
            providing additional context without overwhelming the viewer.
          </span>
        }
      />
      <BrandRow
        label="Button"
        font="Basier Square, Medium"
        letterSpacing="0%"
        lineHeight="120%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={<Button>Button</Button>}
      />
      <BrandRow
        label="Text Button"
        font="Basier Square Mono, Medium"
        letterSpacing="-3%"
        lineHeight="120%"
        borderColor={borderColor}
        secondaryColor={secondaryColor}
        sample={
          <span
            style={{
              fontFamily: '"Basier Square Mono", monospace',
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.2,
              fontSize: 14,
            }}
          >
            Text Button &rarr;
          </span>
        }
      />
    </div>
  );
};

export const BrandGuidelines: Story = {
  name: "Brand Guidelines",
  render: () => <BrandGuidelinesStory />,
};

const FontFamiliesStory = () => {
  const { token } = theme.useToken();
  const borderColor = token.colorBorderSecondary;
  const secondaryColor = token.colorTextDescription;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
      <div>
        <Title level={4}>Basier Square</Title>
        <Text type="secondary">
          Primary font — body text, headings, UI elements
        </Text>
        <Typeset
          fontFamily='"Basier Square", sans-serif'
          fontWeight={400}
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        />
      </div>
      <div>
        <Title level={4}>Basier Square Mono</Title>
        <Text type="secondary">
          Code font — inline code, code blocks, technical identifiers
        </Text>
        <Typeset
          fontFamily='"Basier Square Mono", monospace'
          fontWeight={400}
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        />
      </div>
      <div>
        <Title level={4}>Eliza</Title>
        <Text type="secondary">Display font — brand and marketing use</Text>
        <Typeset
          fontFamily='"Eliza"'
          fontWeight={500}
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        />
      </div>
    </div>
  );
};

export const FontFamilies: Story = {
  name: "Font Families",
  render: () => <FontFamiliesStory />,
};

const ComponentsStory = () => {
  const { token } = theme.useToken();
  const borderColor = token.colorBorderSecondary;
  const secondaryColor = token.colorTextDescription;

  return (
    <div style={{ maxWidth: 960 }}>
      <Title level={4}>Title</Title>
      <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
        Typography.Title — levels 1–5
      </Text>
      <div>
        <ComponentRow
          label="level={1} · 24px"
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        >
          <FidesTypography.Title level={1}>
            Heading Level 1
          </FidesTypography.Title>
        </ComponentRow>
        <ComponentRow
          label="level={2} · 20px"
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        >
          <FidesTypography.Title level={2}>
            Heading Level 2
          </FidesTypography.Title>
        </ComponentRow>
        <ComponentRow
          label="level={3} · 16px"
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        >
          <FidesTypography.Title level={3}>
            Heading Level 3
          </FidesTypography.Title>
        </ComponentRow>
        <ComponentRow
          label="level={4}"
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        >
          <FidesTypography.Title level={4}>
            Heading Level 4
          </FidesTypography.Title>
        </ComponentRow>
        <ComponentRow
          label="level={5}"
          borderColor={borderColor}
          secondaryColor={secondaryColor}
        >
          <FidesTypography.Title level={5}>
            Heading Level 5
          </FidesTypography.Title>
        </ComponentRow>
      </div>

      <div style={{ marginTop: 40 }}>
        <Title level={4}>Text</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          Typography.Text — sizes sm / default / lg
        </Text>
        <div>
          <ComponentRow
            label='size="sm" · 12px'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Text size="sm">
              Small text for captions and labels
            </FidesTypography.Text>
          </ComponentRow>
          <ComponentRow
            label='size="default" · 14px'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Text size="default">
              Default text for body content
            </FidesTypography.Text>
          </ComponentRow>
          <ComponentRow
            label='size="lg" · 18px'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Text size="lg">
              Large text for emphasis
            </FidesTypography.Text>
          </ComponentRow>
        </div>
      </div>

      <div style={{ marginTop: 40 }}>
        <Title level={4}>Paragraph</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          Typography.Paragraph — sizes sm / default / lg
        </Text>
        <div>
          <ComponentRow
            label='size="sm"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Paragraph size="sm">
              Small paragraph for compact layouts and secondary content.
            </FidesTypography.Paragraph>
          </ComponentRow>
          <ComponentRow
            label='size="default"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Paragraph size="default">
              Default paragraph for standard body content and descriptions.
            </FidesTypography.Paragraph>
          </ComponentRow>
          <ComponentRow
            label='size="lg"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Paragraph size="lg">
              Large paragraph for introductions and prominent content.
            </FidesTypography.Paragraph>
          </ComponentRow>
        </div>
      </div>

      <div style={{ marginTop: 40 }}>
        <Title level={4}>Link</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          Typography.Link — default and primary variants, sizes sm / default /
          lg
        </Text>
        <div>
          <ComponentRow
            label='variant="default"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Link href="#">Default link</FidesTypography.Link>
          </ComponentRow>
          <ComponentRow
            label='variant="primary"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Link href="#" variant="primary">
              Primary link
            </FidesTypography.Link>
          </ComponentRow>
          <ComponentRow
            label='size="sm"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Link href="#" size="sm">
              Small link
            </FidesTypography.Link>
          </ComponentRow>
          <ComponentRow
            label='size="lg"'
            borderColor={borderColor}
            secondaryColor={secondaryColor}
          >
            <FidesTypography.Link href="#" size="lg">
              Large link
            </FidesTypography.Link>
          </ComponentRow>
        </div>
      </div>
    </div>
  );
};

export const Components: Story = {
  render: () => <ComponentsStory />,
};
