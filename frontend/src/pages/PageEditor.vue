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
  Paperclip,
  Redo,
  Send,
  Undo,
} from "lucide-vue-next";
import { downloadTxt } from "@/util/download";
import { random, uniqueId } from "lodash";
import Portal from "./portal";
import { agentsWorking } from "@/components/AppAgents.vue";
import type { AgentId } from "@/api/agents";
import { endpoint1, endpoint2, endpoint3 } from "@/api/endpoints";

const { VITE_TITLE: title } = import.meta.env;

const example = "abcde"
  .split("")
  .map((c) =>
    Array(10)
      .fill(null)
      .map(() => c.repeat(random(2, 20)))
      .join(" ")
  )
  .map((p) => `<p>${p}</p>`)
  .join("");

const editor = useEditor({
  content: example,
  enableContentCheck: false,
  parseOptions: {
    preserveWhitespace: "full",
  },
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: "Start writing" }),
    Portal,
  ],
  editorProps: {
    attributes: {
      class:
        "flex-grow-1 flex flex-col gap-5 w-full h-full p-10 focus:outline-none",
    },
  },
});

const getContext = () => {
  if (!editor.value) return;
  const { view, state } = editor.value;
  const { doc, selection } = state;
  const { from, to, $from, $to } = selection;

  const { node } = view.domAtPos($from.pos);
  const { parentElement: p } = node;

  const full = editor.value.getText();

  const sel = doc.textBetween(from, to, "");
  const selP = p?.textContent ?? "";

  const beforeSel = $from.nodeBefore?.textContent;
  const afterSel = $to.nodeAfter?.textContent;

  const pBefore = p?.previousElementSibling?.textContent ?? "";
  const pAfter = p?.nextElementSibling?.textContent ?? "";

  return {
    full,
    sel,
    selP,
    beforeSel,
    afterSel,
    pBefore,
    pAfter,
  };
};

const addPortal = () => {
  if (!editor.value) return;
  const id = "node" + uniqueId();
  editor.value
    .chain()
    .setMeta("addToHistory", false)
    .insertContent({ type: "portal", attrs: { id } })
    .run();
  return id;
};

const findPortal = (id: string) => {
  if (!editor.value) return;
  const { state } = editor.value;
  const { doc } = state;
  const el = document.getElementById(id);
  if (!el) return;
  return findChildren(doc, (node) => node.attrs.id === id)?.[0];
};

type Context = NonNullable<ReturnType<typeof getContext>>;

const action =
  (agents: AgentId[], func: (context: Context) => Promise<string>) =>
  async () => {
    if (!editor.value) return;

    const context = getContext();
    if (!context) return;

    const portalId = addPortal();
    if (!portalId) return;
    agentsWorking.value[portalId] = agents;

    const result = await func(context);

    delete agentsWorking.value[portalId];
    const portalNode = findPortal(portalId);
    if (!portalNode) return;

    editor.value
      .chain()
      .deleteRange({
        from: portalNode.pos,
        to: portalNode.pos + portalNode.node.nodeSize,
      })
      .insertContentAt(portalNode.pos, {
        type: "paragraph",
        content: [{ type: "text", text: result }],
      })
      .run();
  };

const actions = [
  {
    icon: Feather,
    label: "Action 1",
    action: action(
      ["gemini"],
      async ({ full }) => (await endpoint1(full)).output
    ),
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

const overwrite = (text = "") =>
  editor.value?.commands.setContent(text, true, { preserveWhitespace: "full" });

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
