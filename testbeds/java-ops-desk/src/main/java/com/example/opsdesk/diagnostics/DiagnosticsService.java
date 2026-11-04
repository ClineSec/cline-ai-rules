package com.example.opsdesk.diagnostics;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.stereotype.Service;

/** Asks the model for the next read-only diagnostic and runs it on the jump host. */
@Service
public class DiagnosticsService {

    private static final Set<String> SAFE_DIAGNOSTICS = Set.of("uptime", "df -h", "free -m");
    private static final Duration TIMEOUT = Duration.ofSeconds(20);
    private static final String PLANNER = """
            You are a Linux diagnostics planner. Reply with exactly one read-only shell command
            (for example `uptime` or `df -h`) and nothing else.
            """;

    private final ChatModel chatModel;

    public DiagnosticsService(ChatModel chatModel) {
        this.chatModel = chatModel;
    }

    public record DiagnosticResult(String command, int exitCode, String output) {}

    /** Let the model pick the next diagnostic and run it through the shell. */
    public DiagnosticResult nextStep(String symptom) throws IOException, InterruptedException {
        String command = suggest(symptom);
        ProcessBuilder pb = new ProcessBuilder();
        pb.command("/bin/sh", "-c", command);
        pb.redirectErrorStream(true);
        return run(command, pb);
    }

    /** Same planner, but the command must be one of the known-safe diagnostics. */
    public DiagnosticResult checkedStep(String symptom) throws IOException, InterruptedException {
        ChatResponse response = chatModel.call(new Prompt(List.of(
                new SystemMessage(PLANNER), new UserMessage(symptom))));
        String command = response.getResult().getOutput().getText().strip();
        if (!SAFE_DIAGNOSTICS.contains(command)) {
            throw new IllegalArgumentException("refusing unlisted diagnostic: " + command);
        }
        return run(command, new ProcessBuilder(command.split(" ")));
    }

    /** Recent deploys of the service the model thinks is involved. */
    public DiagnosticResult recentDeploys(String symptom) throws IOException, InterruptedException {
        String service = chatModel.call("Which service name best matches this symptom? " + symptom).strip();
        return run(service, new ProcessBuilder("git", "log", "--oneline", "-n", "5", "--", "deploy/" + service));
    }

    private String suggest(String symptom) {
        ChatResponse response = chatModel.call(new Prompt(List.of(
                new SystemMessage(PLANNER), new UserMessage(symptom))));
        return response.getResult().getOutput().getText().strip();
    }

    private DiagnosticResult run(String label, ProcessBuilder pb) throws IOException, InterruptedException {
        Process process = pb.start();
        if (!process.waitFor(TIMEOUT.toSeconds(), TimeUnit.SECONDS)) {
            process.destroyForcibly();
            return new DiagnosticResult(label, -1, "timed out");
        }
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        return new DiagnosticResult(label, process.exitValue(), output);
    }
}
