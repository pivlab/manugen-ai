<template>
  <header
    class="flex gap-1 items-center flex-wrap p-3 sticky top-0 bg-white shadow z-10"
  >
    <AppButton v-tooltip="'Toggle Attachments'" @click="toggleAttachments" :is-active="isAttachmentsOpen">
      <Paperclip />
    </AppButton>
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
    <AppButton v-tooltip="'Toggle Preview'" @click="togglePreview" :is-active="isPreviewOpen">
      <Eye />
    </AppButton>
  </header>


  <main class="flex-grow-1 flex items-stretch gap-5 p-10 relative">
    <!-- blocks interactions until a session is established -->
    <transition name="fade">
      <div v-if="!sessionData" class="overlay">
        <div class="flex flex-col items-center p-5 justify-center h-full">
          <div class="text-white">
            <h2 class="text-xl font-semibold mb-2">Establishing Session...</h2>
            <p v-if="!sessionError">Please wait while we set up your session.</p>
            <p v-else class="text-slate-300">
              Error establishing session: {{ sessionError }}<br /><br />
              Please try refreshing the page or ask your administrator for help.
            </p>
          </div>
        </div>
      </div>
    </transition>

    <AppArtifacts v-if="isAttachmentsOpen"
      class="w-md max-w-1xl flex flex-col gap-2"
      :session="sessionData"
    />

    <EditorContent
      :editor="editor"
      class="flex-grow-1 flex flex-col justify-stretch w-full bg-slate-50 rounded-lg ring-1 ring-slate-500 focus-within:ring-4 focus-within:ring-indigo-500 leading-8 tracking-wide transition-all"
    />

    <AppPreview
      v-if="editor && isPreviewOpen"
      :content="editor?.getText()"
      class="prose prose-sm w-full max-w-2xl flex flex-col gap-2 bg-white rounded-lg ring-1 ring-slate-500 focus-within:ring-4 focus-within:ring-indigo-500 p-5"
    />

    <FloatingMenu
      v-if="editor && cursorActions?.length > 0"
      :editor="editor"
      class="menu"
      :tippy-options="tippyOptions"
    >
      <template
        v-for="({ icon, label, action, type }, index) in cursorActions"
        :key="index"
      >
        <button v-if="type === 'cursor'" class="menu-button" @click="action">
          <component :is="icon" />{{ label }}
        </button>
      </template>
    </FloatingMenu>

    <BubbleMenu
      v-if="editor && selectionActions?.length > 0"
      :editor="editor"
      class="menu"
      :tippy-options="tippyOptions"
    >
      <template
        v-for="({ icon, label, action, type }, index) in selectionActions"
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
import { type ComponentInstance, ref, onMounted } from "vue";
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
import AppArtifacts from "@/components/AppArtifacts.vue";
import AppPreview from "@/components/AppPreview.vue";
import {
  Download,
  Feather,
  Lightbulb,
  Paperclip,
  Eye,
  Redo,
  Sparkles,
  BookX,
  Undo,
  LibraryBig,
  FolderGit2,
} from "lucide-vue-next";
import { downloadTxt } from "@/util/download";
import { uniqueId } from "lodash";
import Portal from "./portal";
import { agentsWorking } from "@/components/AppAgents.vue";
import type { AgentId } from "@/api/agents";
import {  aiWriter, aiWriterAsync } from "@/api/endpoints";
import { type ADKSessionResponse, ensureSessionExists, extractADKText } from "@/api/adk";
import example from "./example.txt?raw";

/** app info */
const { VITE_TITLE: title } = import.meta.env;

/** ADK session init params for the current browser session */
const adkAppName = ref("ai_science_writer")
const adkUsername = ref("test-user")
const adkSessionId = ref<string|null>(null)

/** ADK session data for the established session */
const sessionData = ref<ADKSessionResponse|null>(null);
/** error message if session creation fails */
const sessionError = ref<string|null>(null);

// ensure that a session exists when the page is accessed
onMounted(() => {
  // use the unix timestamp as a unique session id
  const date = Math.floor(Date.now() / 1000);
  adkSessionId.value = `session-${date}`;

  // create a session in ADK and persist it in sessionData
  ensureSessionExists(
    adkAppName.value,
    adkUsername.value,
    adkSessionId.value
  ).then((data) => {
    sessionData.value = data;
    console.log("ADK session created:", data);
  }).catch((error) => {
    console.error("Error creating ADK session:", error);
    sessionError.value = error.message || "Unknown error";
  });
})

// whether the attachments panel is open
const isAttachmentsOpen = ref(false);

const toggleAttachments = () => {
  isAttachmentsOpen.value = !isAttachmentsOpen.value;
};

// whether the preview panel is open
const isPreviewOpen = ref(true);

const togglePreview = () => {
  isPreviewOpen.value = !isPreviewOpen.value;
};

const placeholder =
  "Start writing your manuscript.\n\nSelect some text or start a new paragraph to see AI-assisted actions that can help you generate or revise your content.";

/** tiptap/prosemirror editor instance */
const editor = useEditor({
  content: "",
  parseOptions: { preserveWhitespace: "full" },
  extensions: [
    StarterKit.configure({
      /** disable all default extensions */
      codeBlock: false,
      blockquote: false,
      horizontalRule: false,
      hardBreak: false,
      heading: false,
      italic: false,
      bold: false,
      strike: false,
      bulletList: false,
      orderedList: false,
      listItem: false,
    }), Placeholder.configure({ placeholder }), Portal
  ],
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
  /** actual dom element, not editor node. using familiar dom functionality
   * (e.g. previousElementSibling) turned out to be more straight forward than
   * using built-in tiptap/prosemirror funcs. hacky but necessary to move fast.
   * may want to look into editor.js as simpler alternative, or
   * atlassian/prosemirror-utils.
   */

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

const aiWriterSelectAction = (label: string, icon: any, prefix: string = "", agent: AgentId = "aiWriter") => {
  return {
    icon: icon,
    label: label,
    action: action(
      [agent],
      async ({ sel }) => {
        return extractADKText(
          await aiWriterAsync(`${prefix}${sel}`, sessionData.value)
        )
      }
    ),
    type: "selection",
  }
}

/** actions available to run in editor */
const actions = [
  aiWriterSelectAction("Draft", Feather),
  // * 'reviewer_agent': if the user input includes text '$REFINE_REQUEST$'.
  aiWriterSelectAction("Refine", Sparkles, "$REFINE_REQUEST$ "),
  // * 'retraction_avoidance_agent': if the user input includes text '$RETRACTION_AVOIDANCE_REQUEST$'.
  aiWriterSelectAction("Retracts", BookX, "$RETRACTION_AVOIDANCE_REQUEST$ "),
  // * 'citation_agent': if the user input includes text '$CITATION_REQUEST$'.
  aiWriterSelectAction("Cites", LibraryBig, "$CITATION_REQUEST$ "),
  // * 'repo_agent': if the user input includes text '$REPO_REQUEST$'.
  aiWriterSelectAction("Repos", FolderGit2, "$REPO_REQUEST$ "),
] as const;

// computed properties for cursor and selection actions
const cursorActions = ref(
  actions.filter((a) => a.type === "cursor")
);
const selectionActions = ref(
  actions.filter((a) => a.type === "selection")
);

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
/* Full-page overlay, to block interaction until a session is established */
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7); /* or any semi-transparent shade */
  z-index: 9999;
  pointer-events: all;
}
/* Fade transition styles */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.fade-enter-to, .fade-leave-from {
  opacity: 1;
}

.tiptap p.is-editor-empty:first-child::before {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* force the box to be wider, since we need to accommodate more actions */
.tippy-box { max-width: 600px !important;}

@reference "@/styles.css";

.menu {
  @apply flex gap-2 p-2;
}

.menu-button {
  @apply flex items-center gap-2 px-2 rounded-sm hover:bg-slate-500 transition-all;
}
</style>
