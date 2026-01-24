document.addEventListener("DOMContentLoaded", function () {
    "use strict";
    function updateFiltersAndReload() {
        var url = new URL(window.location.href);
        var params = url.searchParams;

        var keysToDelete = [];
        params.forEach(function (value, key) {
            if (key.startsWith("jsonb_")) {
                keysToDelete.push(key);
            }
        });
        keysToDelete.forEach(function (key) {
            params.delete(key);
        });

        document
            .querySelectorAll(".o_jsonb_filter_checkbox:checked")
            .forEach(function (cb) {
                var attrName = cb.dataset.attrName;
                var paramName = "jsonb_" + attrName;
                var currentValues = params.get(paramName);
                if (currentValues) {
                    params.set(paramName, currentValues + "," + cb.value);
                } else {
                    params.set(paramName, cb.value);
                }
            });

        document.querySelectorAll(".o_jsonb_filter_select").forEach(function (sel) {
            if (sel.value) {
                var attrName = sel.dataset.attrName;
                params.set("jsonb_" + attrName, sel.value);
            }
        });

        params.delete("page");

        window.location.href = url.pathname + "?" + params.toString();
    }

    document.querySelectorAll(".o_jsonb_filter_checkbox").forEach(function (cb) {
        cb.addEventListener("change", updateFiltersAndReload);
    });

    document.querySelectorAll(".o_jsonb_filter_select").forEach(function (sel) {
        sel.addEventListener("change", updateFiltersAndReload);
    });

    document.querySelectorAll(".o_apply_range_filter").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var attrName = btn.dataset.attrName;
            var container = btn.closest(".o_jsonb_range_filter");
            var minInput = container.querySelector(".o_jsonb_range_min");
            var maxInput = container.querySelector(".o_jsonb_range_max");

            var minVal = minInput.value || "";
            var maxVal = maxInput.value || "";

            if (minVal || maxVal) {
                var url = new URL(window.location.href);
                var params = url.searchParams;
                params.set("jsonb_range_" + attrName, minVal + "-" + maxVal);
                params.delete("page");
                window.location.href = url.pathname + "?" + params.toString();
            }
        });
    });
});
