<template>
  <AppButton v-tooltip="tooltip" :disabled="uploading || processing" @click="onClick">
    <LoaderCircle v-if="uploading || processing" class="animate-spin" />
    <Upload v-else />
  </AppButton>
  <input
    ref="input"
    type="file"
    :accept="accept.join(',')"
    :multiple="!single"
    :style="{ display: 'none' }"
    @change="onChange"
  />
</template>

<script setup lang="ts">
/**
 * A slight variant on AppUpload that handles some file types
 * differently and supports loading status also coming from outside
 * the component.
 *
 * (Ideally we'd include this functionality in AppUpload, but i
 * didn't want any changes i made to inadvertently break the existing
 * functionality so soon before the release.)
 */
import { ref, useTemplateRef, watchEffect } from "vue";
import { LoaderCircle, Upload } from "lucide-vue-next";
import { useEventListener } from "@vueuse/core";
import { parsePdf, parseWordDoc, type UploadedFile } from "@/util/upload";
import AppButton from "@/components/AppButton.vue";

type Props = {
  accept: string[];
  tooltip?: string;
  single?: boolean; // if true, forces single-file selection
  processing?: boolean // if true, also shows a loading spinner
};

const props = defineProps<Props>();

const dropZone = ref(document.body);

type Emits = {
  dragging: [boolean];
  files: [{ text: string; filename: string, mimetype: string }[]];
};

const emit = defineEmits<Emits>();

type Slots = {
  default: [{ uploading: boolean }];
};

defineSlots<Slots>();

/** actual file input element */
const input = useTemplateRef("input");

/** dragging state */
const dragging = ref(false);

/** uploading status */
const uploading = ref(false);

/** when dragging state changes */
watchEffect(() => {
  emit("dragging", dragging.value);
  dropZone.value?.classList[dragging.value ? "add" : "remove"]("dragging");
});

const blobToBase64 = (blob: Blob) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        // provides a base64-encoded string with the data URL scheme
        reader.readAsDataURL(blob);
    });
}

/** upload file(s) */
const onLoad = async (fileList: FileList | null) => {
  if (!fileList) return;

  uploading.value = true;

  /** parse each file as appropriate format */
  const files =
    (await Promise.all(
      [...fileList].map(async (file) => {
        let text = "";
        let mimetype = file.type;

        if (file.name.match(/\.(doc|docx)$/)) {
          text = await parseWordDoc(await file.arrayBuffer());
        }
        else if (file.name.match(/\.(pdf)$/)) {
          text = await parsePdf(await file.arrayBuffer());
        }
        else if (file.name.match(/\.(svg)$/)) {
          text = btoa(await file.text());
          mimetype = "image/svg"; // ensure mimetype is set correctly
        }
        else if (file.name.match(/\.(gif|jpg|jpeg|png)$/)) {
          text = await blobToBase64(file) as string;
        }
        else {
          text = await file.text();
        }

        return { text, filename: file.name, mimetype } as UploadedFile;
      })
    ).catch(console.warn)) ?? [];

  uploading.value = false;

  /** notify parent of new files */
  if (files) emit("files", files);

  /** reset file input so the same file could be re-selected */
  if (input.value) input.value.value = "";
};

/** on upload button click */
const onClick = () => input.value?.click();

/** on file input change */
const onChange = (event: Event) =>
  onLoad((event.target as HTMLInputElement).files ?? null);

/** track drag & drop state */
useEventListener(dropZone, "dragenter", () => (dragging.value = true));
useEventListener(dropZone, "dragleave", () => (dragging.value = false));
useEventListener(dropZone, "dragover", (event) => event.preventDefault());

/** when file dropped on drop zone */
useEventListener(dropZone, "drop", (event) => {
  event.preventDefault();
  event.stopPropagation();
  dragging.value = false;
  onLoad(event.dataTransfer?.files ?? null);
});
</script>
