"""Which changed files count as library code when mining fix commits."""
from __future__ import annotations

import pytest

from reviewreplay.mine import _is_code


@pytest.mark.parametrize("path", [
    "src/click/core.py", "src/click/testing.py",              # testing.py is click's library code
    "src/index.ts", "lib/parse.js", "src/Button.tsx", "src/util.mjs", "index.cjs", "src/a.jsx",
    "cmd/root.go", "internal/router/tree.go",
    "src/lib.rs", "src/main/java/com/acme/Parser.java",
])
def test_library_code(path):
    assert _is_code(path)


@pytest.mark.parametrize("path", [
    # Python tests
    "tests/test_core.py", "src/pkg/test_util.py", "pkg/util_test.py", "conftest.py",
    # JS/TS tests
    "src/parse.test.ts", "src/parse.spec.js", "src/__tests__/parse.ts", "src/__mocks__/fs.js",
    "test/index.js",
    # Go tests and fixtures
    "router_test.go", "internal/testdata/sample.go",
    # Java tests
    "src/test/java/com/acme/ParserTest.java", "core/src/main/java/com/acme/ParserTest.java",
    # generated, vendored, built, declarations, minified
    "node_modules/chalk/index.js", "vendor/github.com/x/y.go", "dist/index.js", "build/lib.js",
    "types/index.d.ts", "public/app.min.js",
    # docs, examples and non-code
    "docs/conf.py", "examples/basic/main.go", "README.md", "package.json", "go.mod",
])
def test_not_library_code(path):
    assert not _is_code(path)
