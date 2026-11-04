package com.example.opsdesk.diagnostics;

import java.util.Map;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.expression.EvaluationContext;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.SimpleEvaluationContext;
import org.springframework.stereotype.Component;

/** Turns an on-call engineer's plain-language alert rule into a SpEL condition over metrics. */
@Component
public class AlertRuleEvaluator {

    private static final String RULE_PROMPT =
            "Rewrite this alert rule as one boolean SpEL expression over the map keys cpu, disk, and errors: ";

    private final ChatModel chatModel;
    private final ExpressionParser parser = new SpelExpressionParser();

    public AlertRuleEvaluator(ChatModel chatModel) {
        this.chatModel = chatModel;
    }

    /** Evaluates the model's condition against the latest metrics. */
    public boolean fires(String rule, Map<String, Double> metrics) {
        String condition = chatModel.call(RULE_PROMPT + rule);
        Boolean result = parser.parseExpression(condition).getValue(metrics, Boolean.class);
        return Boolean.TRUE.equals(result);
    }

    /** Same condition, evaluated read-only: property access only, no types or method calls. */
    public boolean firesReadOnly(String rule, Map<String, Double> metrics) {
        String condition = chatModel.call(RULE_PROMPT + rule);
        EvaluationContext context = SimpleEvaluationContext.forReadOnlyDataBinding().build();
        Boolean result = parser.parseExpression(condition).getValue(context, metrics, Boolean.class);
        return Boolean.TRUE.equals(result);
    }
}
