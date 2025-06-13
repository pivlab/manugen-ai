import { mergeAttributes, Node } from "@tiptap/core";

const CustomParagraph = Node.create({
  name: "custom-paragraph",
  group: "block",
  content: "text*",
  parseHTML: () => [{ tag: "p.custom-paragraph" }],
  renderHTML: ({ HTMLAttributes }) => ["p", HTMLAttributes, 0],
  addAttributes: () => ({ id: { default: "" } }),
});

export default CustomParagraph;
