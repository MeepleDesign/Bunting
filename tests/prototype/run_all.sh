#!/bin/bash
# Regression tests for the prototype (prototype/bunting.html), run with Playwright for Python.
# Usage: bash tests/prototype/run_all.sh [test names...]   e.g. bash tests/prototype/run_all.sh tvw tback
# Each script drives the prototype at desktop (1280px) and phone (390px) widths with an in-browser
# fake of the runtime (fixtures/fake.js) and prints FAIL lines or page errors when something breaks.
# ta2 and t21 open two pages that share live data and are occasionally flaky: rerun them alone before investigating.
here="$(cd "$(dirname "$0")" && pwd)"
work="$here/work"; mkdir -p "$work"
cp "$here/../../prototype/bunting.html" "$work/fete-prototype.html"
cp "$here/fixtures/"* "$work/"
cd "$work"
tests=("$@"); [ ${#tests[@]} -eq 0 ] && tests=(t14 t16 t18 t20 t22 tt tv tv2 tc ts tn tp tr2 td ta2 tq tar t21 tvw tvw2 tback)
fail=0
for t in "${tests[@]}"; do
  r=$(timeout 400 python3 "$here/$t.py" 2>&1)
  bad=$(echo "$r" | grep -E "FAIL|Traceback|Error:" | head -3)
  perr=$(echo "$r" | grep -E "errs \[[^]]" | head -2)
  if [ -n "$bad$perr" ]; then echo "✗ $t"; echo "$bad"; echo "$perr"; fail=1; else echo "✓ $t"; fi
done
exit $fail
