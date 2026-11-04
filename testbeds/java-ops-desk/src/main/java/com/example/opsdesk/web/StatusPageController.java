package com.example.opsdesk.web;

import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.http.CacheControl;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.util.HtmlUtils;

/** Drafts customer-facing status page updates from incident timelines. */
@Controller
public class StatusPageController {

    private static final String PAGE = """
            <!doctype html>
            <html><head><title>Status update draft</title></head>
            <body><main class="draft">%s</main></body></html>
            """;

    private final ChatClient chatClient;
    private final Parser markdown = Parser.builder().build();
    private final HtmlRenderer html = HtmlRenderer.builder().softbreak("<br>").build();
    private final HtmlRenderer escapedHtml = HtmlRenderer.builder()
            .escapeHtml(true)
            .sanitizeUrls(true)
            .build();

    public StatusPageController(ChatClient opsChatClient) {
        this.chatClient = opsChatClient;
    }

    @GetMapping("/incidents/{id}/status-draft")
    public ResponseEntity<String> draft(@PathVariable String id) {
        String update = draftUpdate(id);
        String body = PAGE.formatted(html.render(markdown.parse(update)));
        return ResponseEntity.ok()
                .cacheControl(CacheControl.noStore())
                .contentType(MediaType.TEXT_HTML)
                .body(body);
    }

    /** The same draft for the public status page, where nothing raw may get through. */
    @GetMapping("/incidents/{id}/status-public")
    public ResponseEntity<String> publicDraft(@PathVariable String id) {
        String update = chatClient.prompt()
                .user("Write a customer-facing status update for incident " + id + " in markdown.")
                .call()
                .content();
        String body = PAGE.formatted(escapedHtml.render(markdown.parse(update)));
        return ResponseEntity.ok().contentType(MediaType.TEXT_HTML).body(body);
    }

    /** Export used by the old wiki importer, which reads the HTML straight off the socket. */
    @GetMapping("/incidents/{id}/status-export")
    public void export(@PathVariable String id, HttpServletResponse response) throws IOException {
        String update = chatClient.prompt()
                .user("Write a one-line status for incident " + id + ".")
                .call()
                .content();
        response.setContentType(MediaType.TEXT_HTML_VALUE);
        response.setCharacterEncoding("UTF-8");
        try (PrintWriter out = response.getWriter()) {
            out.printf("<p class=\"status\">%s</p>%n", update);
        }
    }

    /** A one-line banner fragment, escaped before it goes into the page. */
    @GetMapping("/incidents/{id}/banner")
    @ResponseBody
    public String banner(@PathVariable String id) {
        String line = chatClient.prompt()
                .user("Write a one-line banner for incident " + id + ".")
                .call()
                .content();
        return "<div class=\"banner\">" + HtmlUtils.htmlEscape(line) + "</div>";
    }

    private String draftUpdate(String id) {
        return chatClient.prompt()
                .user("Write a customer-facing status update for incident " + id + " in markdown.")
                .call()
                .content();
    }
}
