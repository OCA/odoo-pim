from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # custom_specifications_table changed from an inherited view
    # (inherit_id=website_sale_comparison.specifications_table) to a primary
    # standalone template. Remove the stale inherit_id so the upgrade can
    # reload the view without a "cannot be located in parent view" error.
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_ui_view
        SET inherit_id = NULL,
            mode = 'primary'
        WHERE id = (
            SELECT res_id
            FROM ir_model_data
            WHERE module = 'website_attribute_set'
              AND name = 'custom_specifications_table'
              AND model = 'ir.ui.view'
        )
          AND inherit_id IS NOT NULL
        """,
    )
