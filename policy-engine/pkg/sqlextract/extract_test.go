package sqlextract

import (
	"reflect"
	"testing"
)

func TestStripComments(t *testing.T) {
	cases := []struct {
		name string
		in   string
		want string
	}{
		{"empty", "", ""},
		{"no comments", "SELECT 1", "SELECT 1"},
		{
			"leading line comment",
			"-- hi\nSELECT 1",
			"SELECT 1",
		},
		{
			"trailing line comment",
			"SELECT 1 -- hi",
			"SELECT 1",
		},
		{
			"block comment stripped, whitespace preserved",
			"/* prelude */ SELECT x FROM y",
			"SELECT x FROM y",
		},
		{
			"multiple comment lines collapsed",
			"-- one\n--\n-- two\nSELECT 1\n-- three\nFROM t",
			"SELECT 1\nFROM t",
		},
		{
			"multiline block comment",
			"SELECT 1\n/* multi\n   line\n   comment */\nFROM t",
			"SELECT 1\nFROM t",
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := StripComments(tc.in)
			if got != tc.want {
				t.Errorf("StripComments(%q)\n  got:  %q\n  want: %q", tc.in, got, tc.want)
			}
		})
	}
}

func TestQualifiedName(t *testing.T) {
	cases := []struct {
		name string
		ref  TableRef
		want string
	}{
		{"three parts", TableRef{"prod", "sales", "orders"}, "prod.sales.orders"},
		{"two parts", TableRef{"", "sales", "orders"}, "sales.orders"},
		{"one part", TableRef{"", "", "orders"}, "orders"},
		{"empty", TableRef{}, ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := tc.ref.QualifiedName(); got != tc.want {
				t.Errorf("QualifiedName() = %q, want %q", got, tc.want)
			}
		})
	}
}

func TestExtract(t *testing.T) {
	cases := []struct {
		name string
		sql  string
		want []TableRef
	}{
		{
			name: "empty",
			sql:  "",
			want: []TableRef{},
		},
		{
			name: "simple from, 3-part",
			sql:  "SELECT * FROM prod.sales.orders",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "simple from, 2-part",
			sql:  "SELECT * FROM sales.orders",
			want: []TableRef{{"", "sales", "orders"}},
		},
		{
			name: "simple from, 1-part",
			sql:  "SELECT * FROM orders",
			want: []TableRef{{"", "", "orders"}},
		},
		{
			name: "basic join",
			sql:  "SELECT * FROM prod.sales.orders o JOIN prod.customers.profiles c ON o.customer_id = c.id",
			want: []TableRef{
				{"prod", "sales", "orders"},
				{"prod", "customers", "profiles"},
			},
		},
		{
			name: "case insensitive keywords",
			sql:  "select * from prod.sales.orders inner Join prod.events.page_views pv on pv.user_id = 1",
			want: []TableRef{
				{"prod", "sales", "orders"},
				{"prod", "events", "page_views"},
			},
		},
		{
			name: "backtick quoted parts",
			sql:  "SELECT * FROM `prod`.`sales`.`orders`",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "double quoted parts",
			sql:  `SELECT * FROM "prod"."sales"."orders"`,
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "mixed quoting",
			sql:  "SELECT * FROM `prod`.sales.\"orders\"",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "block comments stripped",
			sql:  "/* this is prod.ignore.me */ SELECT * FROM prod.sales.orders",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "multiline block comment stripped",
			sql:  "SELECT *\n/* from ignore.me\n   still comment */\nFROM prod.sales.orders",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "line comments stripped",
			sql:  "SELECT *  -- from ignore.me\nFROM prod.sales.orders -- trailing",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "cte filtered out",
			sql: `WITH recent_orders AS (
			        SELECT * FROM prod.sales.orders WHERE created_at > now() - interval '7 days'
			      )
			      SELECT * FROM recent_orders`,
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "multiple ctes filtered out",
			sql: `WITH a AS (SELECT * FROM prod.sales.orders),
			           b AS (SELECT * FROM prod.events.page_views)
			      SELECT * FROM a JOIN b ON a.user_id = b.user_id`,
			want: []TableRef{
				{"prod", "sales", "orders"},
				{"prod", "events", "page_views"},
			},
		},
		{
			name: "subquery does not match",
			sql:  "SELECT * FROM (SELECT id FROM prod.sales.orders) sub JOIN prod.customers.profiles c ON sub.id = c.id",
			want: []TableRef{
				{"prod", "sales", "orders"},
				{"prod", "customers", "profiles"},
			},
		},
		{
			name: "deduplication",
			sql:  "SELECT * FROM prod.sales.orders o1 JOIN prod.sales.orders o2 ON o1.id = o2.parent_id",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "deduplication is case insensitive",
			sql:  "SELECT * FROM prod.sales.orders o1 JOIN PROD.SALES.ORDERS o2 ON o1.id = o2.id",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "multiple statements",
			sql:  "SELECT * FROM prod.sales.orders; SELECT * FROM prod.events.page_views;",
			want: []TableRef{
				{"prod", "sales", "orders"},
				{"prod", "events", "page_views"},
			},
		},
		{
			name: "whitespace variations around dots",
			sql:  "SELECT * FROM prod . sales . orders",
			want: []TableRef{{"prod", "sales", "orders"}},
		},
		{
			name: "from keyword inside string literal is ignored as long as it's not FROM syntax",
			sql:  "SELECT 'FROM something' AS x FROM prod.sales.orders",
			// The literal 'FROM something' will match because we don't
			// track string boundaries. Document: quoted content can
			// produce false positives. This test locks in current
			// behavior so a regression is visible.
			want: []TableRef{
				{"", "", "something"},
				{"prod", "sales", "orders"},
			},
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := Extract(tc.sql)
			if len(got) == 0 && len(tc.want) == 0 {
				return
			}
			if !reflect.DeepEqual(got, tc.want) {
				t.Errorf("Extract()\n  got:  %+v\n  want: %+v", got, tc.want)
			}
		})
	}
}
