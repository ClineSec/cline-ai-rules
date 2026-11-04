package com.example.opsdesk.reporting;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class ReportQueryServiceTest {

    @Test
    void stripsMarkdownFences() {
        assertThat(ReportQueryService.stripFences("```sql\nSELECT 1\n```")).isEqualTo("SELECT 1");
    }

    @Test
    void leavesPlainSqlAlone() {
        assertThat(ReportQueryService.stripFences("  SELECT 1 ")).isEqualTo("SELECT 1");
    }
}
