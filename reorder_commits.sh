#!/bin/sh
cat > "$1" <<EOF
pick e9f2e7e [MIG] attribute_set: Migration to 19.0
fixup ba829a9 [FIX] attribute_set: fix E501 linting errors
fixup 5e1490f [FIX] attribute_set: Final fixes for Odoo 19 migration
edit aee16db attribute_set:  [FIX] Squashed fixes
pick 3052240 [REF] attribute_set: remove odoo-test-helper
EOF
