package com.example.opsdesk.reporting;

import dev.langchain4j.data.message.SystemMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.chat.response.ChatResponse;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/** Answers ad hoc reporting questions over the read-only incident warehouse. */
@Service
public class ReportQueryService {

    static final String SCHEMA_HINT = """
            You write PostgreSQL for the incident warehouse. Tables: incidents(id, service,
            severity, opened_at, closed_at), pages(incident_id, engineer, paged_at).
            Reply with one SELECT statement and nothing else.
            """;

    private static final Map<String, String> METRICS = Map.of(
            "mttr", "avg(closed_at - opened_at)",
            "volume", "count(*)");

    private static final Set<String> REPORT_TABLES = Set.of("incidents", "pages");

    private final ChatModel model;
    private final JdbcTemplate jdbcTemplate;

    @PersistenceContext
    private EntityManager entityManager;

    public ReportQueryService(ChatModel langchainModel, JdbcTemplate jdbcTemplate) {
        this.model = langchainModel;
        this.jdbcTemplate = jdbcTemplate;
    }

    /** Text-to-SQL: the model writes the whole query. */
    public List<Map<String, Object>> ask(String question) {
        ChatResponse response = model.chat(SystemMessage.from(SCHEMA_HINT), UserMessage.from(question));
        String sql = stripFences(response.aiMessage().text());
        return jdbcTemplate.queryForList(sql);
    }

    /** The model narrows a fixed report with a WHERE clause. */
    @SuppressWarnings("unchecked")
    public List<Object[]> filtered(String question) {
        String where = model.chat("Write only a SQL WHERE condition over incidents(service, severity) for: " + question);
        return nativeRows("SELECT id, service, severity FROM incidents WHERE " + where + " LIMIT 200");
    }

    /** The model only picks a severity, which is bound as a parameter. */
    public List<Map<String, Object>> bySeverity(String question) {
        String severity = model.chat("Answer with one word, sev1 to sev4: " + question).strip();
        return jdbcTemplate.queryForList(
                "SELECT id, service, opened_at FROM incidents WHERE severity = ? ORDER BY opened_at DESC LIMIT 50",
                severity);
    }

    /** The model picks a metric name, mapped to a fixed expression. */
    public List<Map<String, Object>> metric(String question) {
        String choice = model.chat("Answer with one word, mttr or volume: " + question).strip();
        String expression = METRICS.getOrDefault(choice, METRICS.get("volume"));
        return jdbcTemplate.queryForList("SELECT service, " + expression + " AS value FROM incidents GROUP BY service");
    }

    /** The model picks a table, checked against the reporting tables. */
    public Long rowCount(String question) {
        String table = model.chat("Answer with one table name, incidents or pages: " + question).strip();
        if (!REPORT_TABLES.contains(table)) {
            throw new IllegalArgumentException("unknown report table: " + table);
        }
        return jdbcTemplate.queryForObject("SELECT count(*) FROM " + table, Long.class);
    }

    @SuppressWarnings("unchecked")
    private List<Object[]> nativeRows(String sql) {
        return entityManager.createNativeQuery(sql).getResultList();
    }

    static String stripFences(String text) {
        String trimmed = text.strip();
        if (trimmed.startsWith("```")) {
            trimmed = trimmed.replaceFirst("^```(?:sql)?\\s*", "").replaceFirst("\\s*```$", "");
        }
        return trimmed;
    }
}
