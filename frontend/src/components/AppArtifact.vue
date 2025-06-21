<template>
  <div>
      <img v-if="isMimeRoot(props.artifact.mimetype, 'image')" :src="props.artifact.text" :alt="props.artifact.filename" />
      <div v-else>
        <i v-if="isMimeRoot(props.artifact.mimetype, 'text')" class="icon text-icon"></i>
        <i v-else-if="isMimeRoot(props.artifact.mimetype, 'application/pdf')" class="icon pdf-icon"></i>
        <i v-else-if="isMimeRoot(props.artifact.mimetype, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')" class="icon docx-icon"></i>
        <i v-else class="icon file-icon"></i>
      </div>
      <div class="font-bold">{{ props.artifact.filename }}</div>
      <p :class="{ 'cursor-pointer': true, truncate: isTruncated}" @click="toggleTruncate">{{ props.artifact.description }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, onMounted } from "vue";
import type { UploadedFile } from "@/util/upload";

const isTruncated = ref(true);
const toggleTruncate = () => {
  isTruncated.value = !isTruncated.value;
};

type PropTypes = {
  artifact: UploadedFile;
};

// define a prop, name, that specifies the name of the artifact
// define a prop, session, that specifies the session data
const props = defineProps<PropTypes>();

const isMimeRoot = (mimetype: string|null, root: string) => {
  return mimetype && mimetype.startsWith(root + "/");
}
</script>
