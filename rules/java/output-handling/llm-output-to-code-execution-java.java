package com.example.fixtures;

import groovy.lang.GroovyShell;
import groovy.util.Eval;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import jdk.jshell.JShell;
import org.mvel2.MVEL;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.SimpleEvaluationContext;

public class OpsAssistant {

    private static final Set<String> SAFE_COMMANDS = Set.of("uptime", "df -h");
    private static final Map<String, String> PLAYBOOK = Map.of("disk", "df -h", "load", "uptime");

    private final ChatClient chatClient;
    private final ChatModel chatModel;
    private final ScriptEngine engine = new ScriptEngineManager().getEngineByName("groovy");
    private final ExpressionParser parser = new SpelExpressionParser();

    OpsAssistant(ChatClient.Builder builder, ChatModel chatModel) {
        this.chatClient = builder.build();
        this.chatModel = chatModel;
    }

    record Plan(String command, String reason) {}

    void shellString(String question) throws Exception {
        String cmd = chatClient.prompt().user(question).call().content();
        // ruleid: llm-output-to-code-execution-java
        Runtime.getRuntime().exec(cmd);
    }

    void shellViaBash(String question) throws Exception {
        Plan plan = chatClient.prompt().user(u -> u.text(question)).call().entity(Plan.class);
        // ruleid: llm-output-to-code-execution-java
        new ProcessBuilder("bash", "-c", plan.command()).inheritIO().start();
    }

    void shellViaArgvArray(String question) throws Exception {
        String cmd = chatModel.call(new Prompt(question)).getResult().getOutput().getText();
        // ruleid: llm-output-to-code-execution-java
        Runtime.getRuntime().exec(new String[]{"/bin/sh", "-c", cmd});
    }

    void processBuilderSplit(String question) throws Exception {
        String line = chatModel.call(question);
        // ruleid: llm-output-to-code-execution-java
        new ProcessBuilder(line.split(" ")).start();
    }

    void streamed(String question) {
        chatClient.prompt(question).stream().content().subscribe(chunk -> {
            try {
                // ruleid: llm-output-to-code-execution-java
                Runtime.getRuntime().exec(chunk);
            } catch (Exception e) {
                throw new IllegalStateException(e);
            }
        });
    }

    Object scriptEngine(String question) throws Exception {
        String script = chatClient.prompt(question).call().content();
        // ruleid: llm-output-to-code-execution-java
        return engine.eval(script);
    }

    Object groovy(String question) {
        ChatResponse response = chatModel.call(new Prompt(question));
        String code = response.getResult().getOutput().getText();
        // ruleid: llm-output-to-code-execution-java
        return new GroovyShell().evaluate(code);
    }

    Object groovyEval(String question) {
        // ruleid: llm-output-to-code-execution-java
        return Eval.x(Map.of(), chatClient.prompt(question).call().content());
    }

    Object spel(String question) {
        String expr = chatClient.prompt(question).call().content();
        // ruleid: llm-output-to-code-execution-java
        return parser.parseExpression(expr).getValue();
    }

    Object mvel(String question) {
        // ruleid: llm-output-to-code-execution-java
        return MVEL.eval(chatModel.call(question), Map.of());
    }

    void jshell(String question) {
        try (JShell shell = JShell.create()) {
            // ruleid: llm-output-to-code-execution-java
            shell.eval(chatModel.call(question));
        }
    }

    void writeThenRun(String question) throws Exception {
        String script = chatClient.prompt(question).call().content();
        Path file = Files.createTempFile("fix", ".py");
        // ruleid: llm-output-to-code-execution-java
        Files.writeString(file, script);
        new ProcessBuilder("python3", file.toString()).start();
    }

    void inlinePython(String question) throws Exception {
        String code = chatModel.call(question);
        // ruleid: llm-output-to-code-execution-java
        new ProcessBuilder(List.of("python3", "-c", code)).start();
    }

    // Near misses.

    void fixedProgramArgument(String question) throws Exception {
        String ref = chatModel.call(question);
        // ok: llm-output-to-code-execution-java
        new ProcessBuilder("git", "show", ref).start();
        // ok: llm-output-to-code-execution-java
        Runtime.getRuntime().exec(new String[]{"git", "log", "--oneline", ref});
    }

    void allowlisted(String question) throws Exception {
        String cmd = chatModel.call(question).trim();
        if (!SAFE_COMMANDS.contains(cmd)) {
            throw new IllegalArgumentException("not allowed: " + cmd);
        }
        // ok: llm-output-to-code-execution-java
        Runtime.getRuntime().exec(cmd);
    }

    void playbookLookup(String question) throws Exception {
        String key = chatClient.prompt(question).call().content();
        // ok: llm-output-to-code-execution-java
        Runtime.getRuntime().exec(PLAYBOOK.get(key));
    }

    Object spelReadOnly(String question) {
        String expr = chatModel.call(question);
        var context = SimpleEvaluationContext.forReadOnlyDataBinding().build();
        // ok: llm-output-to-code-execution-java
        return parser.parseExpression(expr).getValue(context);
    }

    Object bindingsOnly(String question) throws Exception {
        var bindings = engine.createBindings();
        bindings.put("answer", chatModel.call(question));
        // ok: llm-output-to-code-execution-java
        return engine.eval("answer.length()", bindings);
    }

    void writtenNotRun(String question) throws Exception {
        String notes = chatModel.call(question);
        Path file = Path.of("/tmp/notes.md");
        // ok: llm-output-to-code-execution-java
        Files.writeString(file, notes);
        new ProcessBuilder("git", "add", file.toString()).start();
    }

    void usageOnly(String question) throws Exception {
        ChatResponse response = chatModel.call(new Prompt(question));
        // ok: llm-output-to-code-execution-java
        Runtime.getRuntime().exec(new String[]{"logger", "tokens=" + response.getMetadata().getUsage().getTotalTokens()});
    }
}
