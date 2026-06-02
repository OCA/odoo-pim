By default, the native attributes of a product's attribute set are only
shown in the Attributes tab when the product form is opened from an action
whose context sets `include_native_attribute_view_ref` (the main product
menus of the Product and PIM modules). From any other menu (Sales,
Inventory, Purchase...), only the custom attributes are shown.

To show the native attributes whatever the menu used to open the product
form, go to *Settings \> General Settings \> Attribute Sets* and enable
*Native attributes on every product form*.

When the native attributes are shown, every native attribute that belongs
to an attribute set is removed from its usual place in the product form
and only displayed in the Attributes tab, where it is hidden on products
whose attribute set does not contain it. For example, with `weight` as a
native attribute of some set, products without that set no longer show
their weight. Enabling the setting applies this to every product form.

To show the native attributes only from some menus instead, leave the
setting disabled and add `'include_native_attribute_view_ref': 1` to the
context of the window actions of those menus.
