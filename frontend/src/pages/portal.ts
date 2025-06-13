import { Node } from "@tiptap/core";

/** create custom node that doesn't get cleaned/altered by prosemirror's schema checker */
/** couldn't get tiptap's built-in vue node view to work, and it was more verbose https://tiptap.dev/docs/editor/extensions/custom-extensions/node-views/vue */
const Portal = Node.create({
  name: "portal",
  group: "block",
  content: "block*",
  defining: true,
  atom: true,
  isolating: true,
  selectable: false,
  /** allowed attrs when creating node */
  addAttributes: () => ({ id: { default: "" } }),
  addNodeView:
    () =>
    ({ node }) => {
      /** create blank node with id */
      const dom = document.createElement("div");
      dom.id = node.attrs.id;
      return { dom };
    },
});

export default Portal;
