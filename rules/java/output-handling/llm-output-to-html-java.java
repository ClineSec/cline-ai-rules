package com.example.fixtures;

import jakarta.servlet.http.HttpServletResponse;
import java.io.PrintWriter;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.owasp.encoder.Encode;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.util.HtmlUtils;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/assist")
public class AnswerController {

    private final ChatClient chatClient;
    private final Parser parser = Parser.builder().build();
    private final HtmlRenderer renderer = HtmlRenderer.builder().build();
    private final HtmlRenderer safeRenderer = HtmlRenderer.builder().escapeHtml(true).sanitizeUrls(true).build();

    AnswerController(ChatClient.Builder builder) {
        this.chatClient = builder.build();
    }

    record Answer(String text) {}

    @GetMapping("/answer")
    public String answer(@RequestParam String q) {
        // ruleid: llm-output-to-html-java
        return chatClient.prompt().user(q).call().content();
    }

    @GetMapping("/stream")
    public Flux<String> stream(@RequestParam String q) {
        // ruleid: llm-output-to-html-java
        return chatClient.prompt(q).stream().content();
    }

    @PostMapping(value = "/card", produces = MediaType.TEXT_HTML_VALUE)
    public String card(@RequestParam String q) {
        String markdown = chatClient.prompt(q).call().content();
        String html = renderer.render(parser.parse(markdown));
        // ruleid: llm-output-to-html-java
        return "<div class=\"card\">" + html + "</div>";
    }

    @PostMapping("/preview")
    public ResponseEntity<String> preview(@RequestParam String q) {
        String page = chatClient.prompt(q).call().content();
        // ruleid: llm-output-to-html-java
        return ResponseEntity.ok().contentType(MediaType.TEXT_HTML).body(page);
    }

    @PostMapping("/legacy")
    public void legacy(@RequestParam String q, HttpServletResponse response) throws Exception {
        String reply = chatClient.prompt(q).call().content();
        response.setContentType("text/html;charset=UTF-8");
        PrintWriter out = response.getWriter();
        // ruleid: llm-output-to-html-java
        out.println("<p>" + reply + "</p>");
        // ruleid: llm-output-to-html-java
        out.printf("<footer>%s</footer>", reply);
    }

    @GetMapping("/export")
    public void export(@RequestParam String q, HttpServletResponse response) throws Exception {
        String reply = chatClient.prompt(q).call().content();
        response.setContentType(MediaType.TEXT_HTML_VALUE);
        try (PrintWriter out = response.getWriter()) {
            // ruleid: llm-output-to-html-java
            out.write(reply);
        }
    }

    // Near misses.

    @GetMapping(value = "/plain", produces = MediaType.TEXT_PLAIN_VALUE)
    public String plain(@RequestParam String q) {
        // ok: llm-output-to-html-java
        return chatClient.prompt(q).call().content();
    }

    @GetMapping("/json")
    public Answer json(@RequestParam String q) {
        // ok: llm-output-to-html-java
        return new Answer(chatClient.prompt(q).call().content());
    }

    @PostMapping("/ask")
    public String ask(@RequestParam String q) {
        // ok: llm-output-to-html-java
        return chatClient.prompt(q).call().content();
    }

    @GetMapping("/escaped")
    public String escaped(@RequestParam String q) {
        // ok: llm-output-to-html-java
        return HtmlUtils.htmlEscape(chatClient.prompt(q).call().content());
    }

    @PostMapping(value = "/encoded", produces = "text/html")
    public String encoded(@RequestParam String q) {
        String reply = chatClient.prompt(q).call().content();
        // ok: llm-output-to-html-java
        return "<p>" + Encode.forHtml(reply) + "</p>";
    }

    @PostMapping(value = "/safe-card", produces = MediaType.TEXT_HTML_VALUE)
    public String safeCard(@RequestParam String q) {
        String markdown = chatClient.prompt(q).call().content();
        // ok: llm-output-to-html-java
        return safeRenderer.render(parser.parse(markdown));
    }

    @GetMapping("/text")
    public ResponseEntity<String> text(@RequestParam String q) {
        String reply = chatClient.prompt(q).call().content();
        // ok: llm-output-to-html-java
        return ResponseEntity.ok().contentType(MediaType.TEXT_PLAIN).body(reply);
    }

    @PostMapping("/legacy-text")
    public void legacyText(@RequestParam String q, HttpServletResponse response) throws Exception {
        String reply = chatClient.prompt(q).call().content();
        response.setContentType("text/plain");
        // ok: llm-output-to-html-java
        response.getWriter().write(reply);
    }
}
