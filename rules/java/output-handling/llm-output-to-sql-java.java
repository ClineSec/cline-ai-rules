package com.example.fixtures;

import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.chat.response.ChatResponse;
import dev.langchain4j.data.message.SystemMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.service.AiServices;
import jakarta.persistence.EntityManager;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.List;
import java.util.Map;
import org.jooq.DSLContext;
import org.jooq.impl.DSL;
import org.springframework.jdbc.core.JdbcTemplate;

public class ReportingAssistant {

    interface SqlWriter {
        String write(String question);
    }

    private static final Map<String, String> COLUMNS = Map.of("revenue", "total_cents", "orders", "order_count");

    private final ChatModel model;
    private final JdbcTemplate jdbcTemplate;
    private final EntityManager em;
    private final DSLContext dsl;
    private final Connection connection;
    private final SqlWriter writer;

    ReportingAssistant(ChatModel model, JdbcTemplate jdbcTemplate, EntityManager em, DSLContext dsl, Connection connection) {
        this.model = model;
        this.jdbcTemplate = jdbcTemplate;
        this.em = em;
        this.dsl = dsl;
        this.connection = connection;
        this.writer = AiServices.create(SqlWriter.class, model);
    }

    List<Map<String, Object>> jdbcTemplateQuery(String question) {
        String sql = model.chat(question);
        // ruleid: llm-output-to-sql-java
        return jdbcTemplate.queryForList(sql);
    }

    void plainJdbc(String question) throws Exception {
        ChatResponse response = model.chat(SystemMessage.from("Write one SQL statement."), UserMessage.from(question));
        String sql = response.aiMessage().text();
        try (Statement st = connection.createStatement()) {
            // ruleid: llm-output-to-sql-java
            st.execute(sql);
        }
    }

    List<?> jpql(String question) {
        String where = writer.write(question);
        // ruleid: llm-output-to-sql-java
        return em.createQuery("SELECT o FROM Order o WHERE " + where).getResultList();
    }

    Object jooq(String question) {
        // ruleid: llm-output-to-sql-java
        return dsl.fetch(this.writer.write(question));
    }

    Object jooqField(String question) {
        String expr = model.chat(question);
        // ruleid: llm-output-to-sql-java
        return dsl.select(DSL.field(expr)).from("orders").fetch();
    }

    List<Map<String, Object>> viaHelper(String question) {
        String filter = model.chat(question);
        // ruleid: llm-output-to-sql-java
        return run("SELECT id, status FROM tickets WHERE " + filter);
    }

    void prepared(String question) throws Exception {
        String sql = model.chat(question);
        // ruleid: llm-output-to-sql-java
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.executeQuery();
        }
    }

    // Near misses.

    List<Map<String, Object>> boundParameter(String question) {
        String status = model.chat(question).trim();
        // ok: llm-output-to-sql-java
        return jdbcTemplate.queryForList("SELECT id FROM tickets WHERE status = ?", status);
    }

    List<?> jpqlParameter(String question) {
        String name = model.chat(question);
        // ok: llm-output-to-sql-java
        return em.createQuery("SELECT c FROM Customer c WHERE c.name = :name").setParameter("name", name).getResultList();
    }

    List<Map<String, Object>> allowlistedColumn(String question) {
        String choice = model.chat(question);
        String column = COLUMNS.get(choice);
        // ok: llm-output-to-sql-java
        return jdbcTemplate.queryForList("SELECT day, " + column + " FROM daily_metrics");
    }

    List<Map<String, Object>> checkedIdentifier(String question) {
        String table = model.chat(question);
        if (!table.matches("[a-z_]{1,40}")) {
            throw new IllegalArgumentException("bad table");
        }
        // ok: llm-output-to-sql-java
        return jdbcTemplate.queryForList("SELECT * FROM " + table);
    }

    Object jooqQuoted(String question) {
        String column = model.chat(question);
        // ok: llm-output-to-sql-java
        return dsl.select(DSL.field(DSL.name(column))).from("orders").fetch();
    }

    void logged(String question) {
        String sql = model.chat(question);
        // ok: llm-output-to-sql-java
        System.out.println("SELECT preview: " + sql);
    }

    void usage(String question) throws Exception {
        ChatResponse response = model.chat(UserMessage.from(question));
        // ok: llm-output-to-sql-java
        jdbcTemplate.update("INSERT INTO usage(tokens) VALUES (" + response.tokenUsage().totalTokenCount() + ")");
    }

    private List<Map<String, Object>> run(String sql) {
        return jdbcTemplate.queryForList(sql);
    }
}
