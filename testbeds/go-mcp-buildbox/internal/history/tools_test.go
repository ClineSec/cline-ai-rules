package history

import "testing"

func TestSortColumnsAreColumnNames(t *testing.T) {
	for name, column := range sortColumns {
		for _, r := range column {
			if !(r == '_' || (r >= 'a' && r <= 'z')) {
				t.Errorf("sort %q maps to %q, which is not a plain column name", name, column)
			}
		}
	}
}

func TestJSONResult(t *testing.T) {
	res, err := jsonResult([]FlakyTest{{Suite: "api", Name: "TestRetry", FailRate: 0.25}})
	if err != nil {
		t.Fatal(err)
	}
	if res.IsError {
		t.Fatal("unexpected error result")
	}
}
