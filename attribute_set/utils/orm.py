# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json

from odoo.tools.safe_eval import safe_eval


def transfer_field_to_modifiers(field, modifiers):
    default_values = {}
    state_exceptions = {}
    for attr in ("invisible", "readonly", "required"):
        state_exceptions[attr] = []
        default_values[attr] = bool(field.get(attr))
    for state, modifs in field.get("states", {}).items():
        for modif in modifs:
            if default_values[modif[0]] != modif[1]:
                state_exceptions[modif[0]].append(state)

    for attr, default_value in default_values.items():
        if state_exceptions[attr]:
            modifiers[attr] = [
                ("state", "not in" if default_value else "in", state_exceptions[attr])
            ]
        else:
            modifiers[attr] = default_value


# Don't deal with groups, it is done by check_group().
# Need the context to evaluate the invisible attribute on tree views.
# For non-tree views, the context shouldn't be given.
def transfer_node_to_modifiers(node, modifiers, context=None, in_tree_view=False):
    if node.get("attrs"):
        modifiers.update(safe_eval(node.get("attrs")))

    if node.get("states"):
        if "invisible" in modifiers and isinstance(modifiers["invisible"], list):
            # TODO combine with AND or OR, use implicit AND for now.
            modifiers["invisible"].append(
                ("state", "not in", node.get("states").split(","))
            )
        else:
            modifiers["invisible"] = [
                ("state", "not in", node.get("states").split(","))
            ]

    for a in ("invisible", "readonly", "required"):
        if node.get(a):
            v = bool(safe_eval(node.get(a), {"context": context or {}}))
            if in_tree_view and a == "invisible":
                # Invisible in a tree view has a specific meaning, make it a
                # new key in the modifiers attribute.
                modifiers["column_invisible"] = v
            elif v or (a not in modifiers or not isinstance(modifiers[a], list)):
                # Don't set the attribute to False if a dynamic value was
                # provided (i.e. a domain from attrs or states).
                modifiers[a] = v


def simplify_modifiers(modifiers):
    for a in ("invisible", "readonly", "required"):
        if a in modifiers and not modifiers[a]:
            del modifiers[a]


def transfer_modifiers_to_node(modifiers, node):
    if modifiers:
        simplify_modifiers(modifiers)
        node.set("modifiers", json.dumps(modifiers))


def setup_modifiers(node, field=None, context=None, in_tree_view=False):
    """Generate ``modifiers``  from node attributes and fields descriptors.
    Alters its first argument in-place.
    :param node: ``field`` node from an OpenERP view
    :type node: lxml.etree._Element
    :param dict field: field descriptor corresponding to the provided node
    :param dict context: execution context used to evaluate node attributes
    :param bool in_tree_view: triggers the ``column_invisible`` code
                              path (separate from ``invisible``): in
                              tree view there are two levels of
                              invisibility, cell content (a column is
                              present but the cell itself is not
                              displayed) with ``invisible`` and column
                              invisibility (the whole column is
                              hidden) with ``column_invisible``.
    :returns: None
    """
    modifiers = {}
    if field is not None:
        transfer_field_to_modifiers(field, modifiers)
    transfer_node_to_modifiers(
        node, modifiers, context=context, in_tree_view=in_tree_view
    )
    transfer_modifiers_to_node(modifiers, node)
