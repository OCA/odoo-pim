To configure the dynamic wizard, go to
`PIM > Product Wizard Settings > Questions` as a PIM manager.

Wizard configuration can be a bit tricky as more features are added.
As of now, available question attributes include:

* **Name**: Question name, shown in the bottom-right of the wizard
  to help with maintenance (especially if a screenshot is taken).
* **Parent question**: Questions can be nested like a tree. If the parent
  condition passes, its branch will be processed; otherwise, child questions
  are skipped.
* **Is Automatic**: Hides the question from the user and allows setting
  values automatically.
* **Question**: The actual prompt shown to the user, unless it's automatic.
* **Sequence**: Defines the question order within its branch.
* **Question Type**:

  - **Field** – sets a product template field
  - **Custom** – lets the user choose from a custom set of values
  - **Logical** – groups multiple field updates under one step and/or
    organize questions
* **Is Conditional**: Only displays the step and children if the condition
  is met (requires a non-logical parent).
* **Answer Required**: Forces the user to provide an answer before proceeding.

**Apply If (page)**: Setup condition (display if *Is conditional* is checked )

* **Conditional Operator**: Currently supports `==` and `!=`.
* **Expected result**: The value to match on the parent question. For:

  - **Custom** – select from predefined values
  - **Field** – use the technical value (`666` for many2one,
    `True`/`False` for booleans, technical value on field selection ie:
    `product` / `service` / `consu`, ...)

**Product Attribute (page)**: Shown if *Question Type* is **Field**.

* **Field**: Product template field to set
* **Display Field Name**: Show/hide the field label in the wizard
* **Default Value**: A string, depending on field type:

  - many2one → record ID (e.g., `1`)
  - boolean → `true` for checked/true value, empty string or `false` for unchecked/false value 
  - x2m → valid JSON string (e.g. `[[0, 0, {"name": "Box 20", "qty": 20}]]`)
* **Custom View**: XML snippet to control how the field is rendered::

    <field
        name="packaging_ids"
        nolabel="1"
        context="{'tree_view_ref':'product.product_packaging_tree_view2', 'form_view_ref':'product.product_packaging_form_view2', 'default_name': 'Box of 10', 'default_qty': 10}"
    />

**Custom Response (page)**: Shown if *Question Type* is **Custom**

* List of valid responses
* **Default Answer**: Can be set after the question is saved

**Values (page)**: Shown if *Question Type* is **Logical**

* **Default Values**: Only set values that aren't already defined by a previous step (even False or empty string counts as defined)
* **Values**: Always override values, even if already set by another step. JSON format (e.g. `{"type": "product", "company_id": current_company_id}`)

**Children Questions**: Executed only if the parent condition is met.

.. note::

    If a name is defined, it will be used as the wizard's title.
    It's a good idea to ask for the product name first, so users remember what they’re doing.

Special `company_id` cases:

* `company_id` is auto-set by the module to the current company; a different default will be ignored.
* You can use special variable `current_company_id` that will be replaced by the id of the company_id already
  set. this can be used in
  * default values for x2m fields to set the company_id
  * in custom view to set the default_company_id in context key
  * in logical values for x2m fields
