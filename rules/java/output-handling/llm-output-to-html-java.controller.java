package com.example.fixtures;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class DigestPageController {

    private final ChatClient chatClient;

    DigestPageController(ChatClient chatClient) {
        this.chatClient = chatClient;
    }

    @GetMapping("/digest/{week}")
    public ResponseEntity<String> digest(@PathVariable String week) {
        String text = chatClient.prompt("Summarize incidents for week " + week).call().content();
        // ruleid: llm-output-to-html-java
        return ResponseEntity.ok(text);
    }

    @GetMapping("/digest/{week}.txt")
    public ResponseEntity<String> digestText(@PathVariable String week) {
        String text = chatClient.prompt("Summarize incidents for week " + week).call().content();
        // ok: llm-output-to-html-java
        return ResponseEntity.ok().contentType(MediaType.TEXT_PLAIN).body(text);
    }

    @GetMapping("/digest")
    public String digestView() {
        // ok: llm-output-to-html-java
        return "digest";
    }
}
