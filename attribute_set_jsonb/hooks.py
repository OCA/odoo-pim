def post_init_hook(env):
    """Index the serialization fields created before this module.

    base_sparse_field_jsonb takes care of the JSONB conversion, and creates a
    GIN index for the serialized fields having ``index`` set.
    """
    env["attribute.attribute"].search(
        [("serialized", "=", True)]
    )._index_serialization_field()
