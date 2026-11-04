<script setup lang="ts">
import { onMounted, ref } from "vue";
import mermaid from "mermaid";
import katex from "katex";

const props = defineProps<{ diagram: string; formula: string }>();
const diagramEl = ref<HTMLElement>();
const formulaHtml = ref("");

mermaid.initialize({
  startOnLoad: false,
  // ruleid: mermaid-or-katex-unsafe-config-markup
  securityLevel: 'loose',
});

onMounted(async () => {
  const { svg } = await mermaid.render("answer-diagram", props.diagram);
  if (diagramEl.value) diagramEl.value.innerHTML = svg;
  formulaHtml.value = katex.renderToString(props.formula, {
    // ruleid: mermaid-or-katex-unsafe-config-markup
    trust: () => true,
  });
});
</script>

<template>
  <div ref="diagramEl" class="diagram" />
  <!-- ok: mermaid-or-katex-unsafe-config-markup -->
  <MermaidView :config="{ theme: 'neutral', securityLevel: 'strict' }" :source="diagram" />
  <span v-html="formulaHtml" />
</template>
