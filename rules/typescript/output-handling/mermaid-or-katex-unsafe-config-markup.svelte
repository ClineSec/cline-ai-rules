<script>
  import { onMount } from "svelte";
  import mermaid from "mermaid";

  export let source = "";
  let container;

  onMount(async () => {
    // ok: mermaid-or-katex-unsafe-config-markup
    mermaid.initialize({ startOnLoad: false, securityLevel: "sandbox" });
    const { svg } = await mermaid.render("chat-diagram", source);
    container.innerHTML = svg;
  });

  // ruleid: mermaid-or-katex-unsafe-config-markup
  const interactive = { startOnLoad: false, "securityLevel": "loose" };
</script>

<div bind:this={container} class="diagram"></div>
