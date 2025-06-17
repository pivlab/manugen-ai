import { createRouter, createWebHistory } from "vue-router";
import PageEditor from "@/pages/PageEditor.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: PageEditor,
    },
  ],
});

export default router;
