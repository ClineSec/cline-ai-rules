package com.example.opsdesk.config;

import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AiConfig {

    static final String DESK_POLICY = """
            You are the operations desk assistant. Answer from the runbooks you are given.
            Never suggest commands that change state; read-only diagnostics only.
            """;

    @Bean
    ChatClient opsChatClient(ChatClient.Builder builder) {
        return builder.defaultSystem(DESK_POLICY).build();
    }

    @Bean
    ChatModel langchainModel(@Value("${opsdesk.langchain4j.base-url}") String baseUrl,
                             @Value("${opsdesk.langchain4j.model}") String model) {
        return OpenAiChatModel.builder()
                .baseUrl(baseUrl)
                .apiKey(System.getenv("OPENAI_API_KEY"))
                .modelName(model)
                .temperature(0.0)
                .build();
    }
}
