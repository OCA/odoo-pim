"""
Diagnostic test to verify whether test models affect the ORM.

This test checks if res.partner has attribute_set_id field WITH and WITHOUT
test models loaded.
"""

import logging

from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)


class DiagnosticOrmTest(TransactionCase):
    """Diagnoses whether test models are affecting the ORM registry."""

    def test_01_attribute_set_id_missing_without_test_models(self):
        """Test 1: Check if attribute_set_id exists without test model imports."""
        res_partner_model = self.env["res.partner"]

        # List all fields on res.partner
        fields = res_partner_model.fields_get()
        field_names = list(fields.keys())

        self.assertIn("id", field_names, "Basic fields should exist on res.partner")

        has_attribute_set_id = "attribute_set_id" in field_names

        _logger.info("\n" + "=" * 80)
        _logger.info("TEST 1: Check attribute_set_id on res.partner")
        _logger.info("(NO test models imported)")
        _logger.info("=" * 80)
        _logger.info(f"Fields on res.partner: {len(field_names)} total")
        _logger.info(f"attribute_set_id present: {has_attribute_set_id}")
        if not has_attribute_set_id:
            _logger.info("attribute_set_id NOT FOUND - THIS IS THE PROBLEM")
            _logger.info("Test models are NOT affecting the ORM")
        else:
            _logger.info("attribute_set_id FOUND - models are somehow loaded")
        _logger.info("=" * 80 + "\n")

        # Don't fail here - we EXPECT it to be missing
        # The point is to diagnose, not to pass/fail yet

    def test_02_verify_mixin_exists(self):
        """Test 2: Verify that the mixin model exists in the registry."""
        try:
            mixin_model = self.env["attribute.set.owner.mixin"]
            _logger.info("\n" + "=" * 80)
            _logger.info("TEST 2: Check attribute.set.owner.mixin")
            _logger.info("=" * 80)
            _logger.info(f"Mixin model exists: {mixin_model}")

            # Check if mixin has the field
            fields = mixin_model.fields_get()
            has_field = "attribute_set_id" in fields
            _logger.info(f"Mixin has attribute_set_id field: {has_field}")
            _logger.info("=" * 80 + "\n")
        except Exception as e:
            _logger.info("\n" + "=" * 80)
            _logger.info("TEST 2: Check attribute.set.owner.mixin")
            _logger.info("=" * 80)
            _logger.info(f"Error accessing mixin: {e}")
            _logger.info("=" * 80 + "\n")

    def test_03_check_res_partner_inheritance(self):
        """Test 3: Check what models res.partner has inherited from."""
        res_partner_model = self.env["res.partner"]

        # Check the _inherit chain
        _logger.info("\n" + "=" * 80)
        _logger.info("TEST 3: res.partner inheritance chain")
        _logger.info("=" * 80)
        _logger.info(f"Model name: {res_partner_model._name}")
        inherit_specs = (
            res_partner_model._inherit
            if hasattr(res_partner_model, "_inherit")
            else "None"
        )
        _logger.info(f"Inherit specifications: {inherit_specs}")

        # Get all parent classes to see inheritance
        _logger.info("Python MRO (Method Resolution Order):")
        for cls in type(res_partner_model).__mro__[:-1]:
            _logger.info(f"  - {cls.__name__}")
        _logger.info("=" * 80 + "\n")

    def test_04_try_to_create_view_with_attribute_set_id(self):
        """Test 4: Create a view that references attribute_set_id."""
        _logger.info("\n" + "=" * 80)
        _logger.info("TEST 4: Try to create view with field reference")
        _logger.info("=" * 80)

        try:
            view = self.env["ir.ui.view"].create(
                {
                    "name": "res.partner.form.diagnostic",
                    "model": "res.partner",
                    "inherit_id": self.env.ref("base.view_partner_form").id,
                    "arch": """
                        <xpath expr="//notebook" position="inside">
                            <page name="test_attributes">
                                <field name="attribute_set_id"/>
                            </page>
                        </xpath>
                    """,
                }
            )
            _logger.info(f"View created successfully: {view.id}")
            _logger.info("attribute_set_id was recognized on res.partner")
            _logger.info("=" * 80 + "\n")
        except Exception as e:
            _logger.info(f"View creation FAILED: {type(e).__name__}")
            _logger.info(f"Error message: {str(e)[:200]}")
            _logger.info("This is the actual error in the real test")
            _logger.info("=" * 80 + "\n")
