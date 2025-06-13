import { Node } from "@tiptap/core";

const Portal = Node.create({
  name: "portal",
  group: "block",
  content: "block*",
  defining: true,
  atom: true,
  isolating: true,
  selectable: false,
  addAttributes: () => ({ id: { default: "" } }),
  addNodeView:
    () =>
    ({ node }) => {
      const dom = document.createElement("div");
      dom.id = node.attrs.id;
      return { dom };
    },
});

export default Portal;
