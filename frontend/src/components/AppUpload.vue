<template>
  <AppButton
    v-tooltip="tooltip"
    :disabled="uploading"
    @click="onClick"
  >
    <LoaderCircle v-if="uploading" class="spin" />
    <Upload v-else />
  </AppButton>
  <input
    ref="input"
    type="file"
    :accept="accept.join(',')"
    multiple
    :style="{ display: 'none' }"
    @change="onChange"
  />
</template>

<script setup lang="ts">
import { ref, useTemplateRef, watchEffect } from "vue";
import { LoaderCircle, Upload } from "lucide-vue-next";
import { useEventListener } from "@vueuse/core";
import { parsePdf, parseWordDoc } from "@/util/upload";
import AppButton from "./AppButton.vue";

type Props = {
  accept: string[];
  tooltip?: string;
};

defineProps<Props>();

const dropZone = ref(document.body);

type Emits = {
  dragging: [boolean];
  files: [{ text: string; filename: string }[]];
};

const emit = defineEmits<Emits>();

type Slots = {
  default: [{ uploading: boolean }];
};

defineSlots<Slots>();

const input = useTemplateRef("input");

const dragging = ref(false);

const uploading = ref(false);

watchEffect(() => {
  emit("dragging", dragging.value);
  dropZone.value?.classList[dragging.value ? "add" : "remove"]("dragging");
});

const onLoad = async (fileList: FileList | null) => {
  if (!fileList) return;

  uploading.value = true;

  const files =
    (await Promise.all(
      [...fileList].map(async (file) => {
        let text = "";

        if (file.name.match(/\.(doc|docx)$/))
          text = await parseWordDoc(await file.arrayBuffer());
        else if (file.name.match(/\.(pdf)$/))
          text = await parsePdf(await file.arrayBuffer());
        else text = await file.text();

        return { text, filename: file.name };
      })
    ).catch(console.warn)) ?? [];

  uploading.value = false;

  if (files) emit("files", files);

  if (input.value) input.value.value = "";
};

const onClick = () => input.value?.click();

const onChange = (event: Event) =>
  onLoad((event.target as HTMLInputElement).files ?? null);

useEventListener(dropZone, "dragenter", () => (dragging.value = true));
useEventListener(dropZone, "dragleave", () => (dragging.value = false));
useEventListener(dropZone, "dragover", (event) => event.preventDefault());

useEventListener(dropZone, "drop", (event) => {
  event.preventDefault();
  event.stopPropagation();
  dragging.value = false;
  onLoad(event.dataTransfer?.files ?? null);
});
</script>
