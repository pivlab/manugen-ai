<template>
  <header
    class="flex gap-1 items-center flex-wrap p-3 sticky top-0 bg-white shadow z-10"
  >
    <AppButton v-tooltip="'Undo'" @click="editor?.commands.undo()">
      <Undo />
    </AppButton>
    <AppButton v-tooltip="'Redo'" @click="editor?.commands.redo()">
      <Redo />
    </AppButton>
    <AppButton v-tooltip="'Try an example'" @click="overwrite(example)">
      <Lightbulb />
    </AppButton>

    <h1
      class="flex-grow-1 text-center text-lg font-light tracking-wider uppercase"
    >
      {{ title }}
    </h1>

    <AppUpload
      tooltip="Upload document, or drag & drop onto page"
      :accept="accept"
      @files="(files) => overwrite(files[0]?.text)"
    />
    <AppButton
      v-tooltip="'Download manuscript'"
      @click="downloadTxt(editor?.getText() ?? '', `${title} Manuscript`)"
    >
      <Download />
    </AppButton>
  </header>

  <main class="flex-grow-1 flex flex-col items-center gap-5 p-10">
    <EditorContent
      :editor="editor"
      class="flex-grow-1 flex flex-col justify-stretch w-full max-w-4xl bg-slate-50 rounded-lg ring-1 ring-slate-500 focus-within:ring-4 focus-within:ring-indigo-500 leading-8 tracking-wide transition-all"
    />

    <FloatingMenu
      v-if="editor"
      :editor="editor"
      class="menu"
      :tippy-options="tippyOptions"
    >
      <template
        v-for="({ icon, label, action, type }, index) in actions"
        :key="index"
      >
        <button v-if="type === 'cursor'" class="menu-button" @click="action">
          <component :is="icon" />{{ label }}
        </button>
      </template>
    </FloatingMenu>

    <BubbleMenu
      v-if="editor"
      :editor="editor"
      class="menu"
      :tippy-options="tippyOptions"
    >
      <template
        v-for="({ icon, label, action, type }, index) in actions"
        :key="index"
      >
        <button v-if="type === 'selection'" class="menu-button" @click="action">
          <component :is="icon" />{{ label }}
        </button>
      </template>
    </BubbleMenu>

    <AppAgents />
  </main>
</template>

<script setup lang="ts">
import { type ComponentInstance } from "vue";
import {
  useEditor,
  BubbleMenu,
  EditorContent,
  FloatingMenu,
  findChildren,
} from "@tiptap/vue-3";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import AppUpload from "@/components/AppUpload.vue";
import AppButton from "@/components/AppButton.vue";
import AppAgents from "@/components/AppAgents.vue";
import {
  Download,
  Feather,
  Lightbulb,
  Paperclip,
  Redo,
  Send,
  Undo,
} from "lucide-vue-next";
import { downloadTxt } from "@/util/download";
import { uniqueId } from "lodash";
import Portal from "./portal";
import { agentsWorking } from "@/components/AppAgents.vue";
import type { AgentId } from "@/api/agents";
import { endpoint1, endpoint2, endpoint3 } from "@/api/endpoints";
import example from "./example.txt?raw";

/** app info */
const { VITE_TITLE: title } = import.meta.env;

const placeholder =
  "Start writing your manuscript.\n\nSelect some text or start a new paragraph to see AI-assisted actions that can help you generate or revise your content.";

/** tiptap/prosemirror editor instance */
const editor = useEditor({
  content: "",
  parseOptions: { preserveWhitespace: "full" },
  extensions: [StarterKit, Placeholder.configure({ placeholder }), Portal],
  editorProps: {
    attributes: {
      /** style of immediate child of editor root element (EditorContent) */
      class:
        "flex-grow-1 flex flex-col gap-5 w-full h-full p-10 focus:outline-none",
    },
  },
});

/** get info about state of document and selection */
const getContext = () => {
  if (!editor.value) return;

  /** methods and props from editor */
  const { view, state } = editor.value;
  const { doc, selection } = state;
  const { from, to, $from, $to } = selection;

  /** get node at selection start */
  const { node } = view.domAtPos($from.pos);

  /** "current" paragraph that selection is in */
  const { parentElement: p } = node;

  return {
    /** full text content of editor */
    full: editor.value.getText(),

    /** selected text */
    sel: doc.textBetween(from, to, ""),
    /** current paragraph text */
    selP: p?.textContent ?? "",

    /** text before selection in current paragraph */
    beforeSel: $from.nodeBefore?.textContent,
    /** text after selection in current paragraph */
    afterSel: $to.nodeAfter?.textContent,

    /** text of paragraph before current paragraph */
    pBefore: p?.previousElementSibling?.textContent ?? "",
    /** text of paragraph after current paragraph */
    pAfter: p?.nextElementSibling?.textContent ?? "",
  };
};

type Context = NonNullable<ReturnType<typeof getContext>>;

/** add blank node for arbitrary content to be rendered into */
const addPortal = () => {
  if (!editor.value) return;
  /** unique id for node */
  const id = "node" + uniqueId();
  editor.value
    .chain()
    /** prevent undo */
    .setMeta("addToHistory", false)
    /** insert node into editor */
    .insertContent({ type: "portal", attrs: { id } })
    .run();
  /** return id so node can be cleaned up later */
  return id;
};

/** find editor node corresponding to dom node with id */
const findPortal = (id: string) => {
  if (!editor.value) return;
  const { state } = editor.value;
  const { doc } = state;
  const el = document.getElementById(id);
  if (!el) return;
  return findChildren(doc, (node) => node.attrs.id === id)?.[0];
};

/** create func that runs an action and handles placeholder in the editor while its working */
const action =
  (
    /** ids of agents that are involved in this action */
    agents: AgentId[],
    /** actual work to run */
    func: (context: Context) => Promise<string>
  ) =>
  async () => {
    if (!editor.value) return;

    /** get context info */
    const context = getContext();
    if (!context) return;

    /** create portal */
    const portalId = addPortal();
    if (!portalId) return;

    /** tell agents component that these agents are working in this portal */
    agentsWorking.value[portalId] = agents;

    /** run actual work func, providing context */
    const result = await func(context);

    /** tell agents component that work is done */
    delete agentsWorking.value[portalId];

    /** find node of portal created earlier */
    const portalNode = findPortal(portalId);
    if (!portalNode) return;

    editor.value
      .chain()
      /** delete portal node */
      .deleteRange({
        from: portalNode.pos,
        to: portalNode.pos + portalNode.node.nodeSize,
      })
      /** insert response in its place */
      .insertContentAt(portalNode.pos, {
        type: "paragraph",
        content: [{ type: "text", text: result }],
      })
      .run();
  };

/** actions available to run in editor */
const actions = [
  {
    /** icon to show popup */
    icon: Feather,
    /** label to show in popup */
    label: "Action 1",
    action: action(
      ["gemini"],
      async ({ full }) =>
        /** run actual work on backend */
        (await endpoint1(full)).output
    ),
    /** whether action appears when text selected, or just single cursor position */
    type: "selection",
  },
  {
    icon: Paperclip,
    label: "Action 2",
    action: action(
      ["gemini", "chatgpt"],
      async ({ sel }) => (await endpoint2(sel)).output
    ),
    type: "cursor",
  },
  {
    icon: Send,
    label: "Action 3",
    action: action(
      ["claude"],
      async ({ pBefore }) => (await endpoint3(pBefore)).output
    ),
    selection: true,
    type: "cursor",
  },
] as const;

/** replace text content of entire editor */
const overwrite = (text = "") =>
  editor.value?.commands.setContent(text, true, { preserveWhitespace: "full" });

/** upload file types */
const accept = [
  ".txt",
  ".doc",
  ".docx",
  ".pdf",
  "text/plain",
  "application/pdf",
  "application/msword",
];

type TippyOptions = ComponentInstance<
  typeof BubbleMenu
>["$props"]["tippyOptions"];

/** options for editor popups */
const tippyOptions: TippyOptions = { placement: "bottom" };
</script>

<style>
.tiptap p.is-editor-empty:first-child::before {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

@reference "@/styles.css";

.menu {
  @apply flex gap-2 p-2;
}

.menu-button {
  @apply flex items-center gap-2 px-2 rounded-sm hover:bg-slate-500 transition-all;
}
</style>
