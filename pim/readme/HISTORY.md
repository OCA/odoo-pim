## 19.0.1.1.0 (2026-08-06)

- Grant the PIM roles the access rights their descriptions promise. **PIM
  Manager** can now create/edit attribute sets, groups, attributes and options
  (previously only `base.group_erp_manager` could, so a PIM Manager saw the menus
  but hit AccessError on create/write -- the role was non-functional without the
  admin group), and **PIM User** can edit products. Adds the missing
  `ir.model.access.csv`.
