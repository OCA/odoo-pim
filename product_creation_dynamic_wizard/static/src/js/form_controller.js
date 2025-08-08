odoo.define("product_creation_dynamic_wizard.form_controller", function (require) {
    "use strict";
    var core = require("web.core");
    var FormController = require("web.FormController");
    var qweb = core.qweb;
    // Templatize FormView.buttons instead of hardcoding them, much like TreeController and KanbanController
    FormController.include({
        buttons_template: "FormView.buttons",
        // This method is a full copy of parent, with one line changed (see inline comment)
        renderButtons: function ($node) {
            var $footer = this.footerToButtons
                ? this.renderer.$el && this.renderer.$("footer")
                : null;
            var mustRenderFooterButtons = $footer && $footer.length;
            if ((this.defaultButtons && !this.$buttons) || mustRenderFooterButtons) {
                this.$buttons = $("<div/>");
                if (mustRenderFooterButtons) {
                    this.$buttons.append($footer);
                } else {
                    // Changed line
                    this.$buttons.append(
                        qweb.render(this.buttons_template, {widget: this})
                    );
                    this.$buttons.on(
                        "click",
                        ".o_form_button_edit",
                        this._onEdit.bind(this)
                    );
                    this.$buttons.on(
                        "click",
                        ".o_form_button_create",
                        this._onCreate.bind(this)
                    );
                    this.$buttons.on(
                        "click",
                        ".o_form_button_save",
                        this._onSave.bind(this)
                    );
                    this.$buttons.on(
                        "click",
                        ".o_form_button_cancel",
                        this._onDiscard.bind(this)
                    );
                    this._assignSaveCancelKeyboardBehavior(
                        this.$buttons.find(".o_form_buttons_edit")
                    );
                    this.$buttons.find(".o_form_buttons_edit").tooltip({
                        delay: {show: 200, hide: 0},
                        title: function () {
                            return qweb.render("SaveCancelButton.tooltip");
                        },
                        trigger: "manual",
                    });
                }
            }
            if (this.$buttons && $node) {
                this.$buttons.appendTo($node);
            }
        },
    });
});
