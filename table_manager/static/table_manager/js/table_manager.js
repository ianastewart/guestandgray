// Handle checkboxes in tables, and modal forms
$(document).ready(function () {
    'use strict';
    let last_path = "";
    let lastChecked = null;
    let chkboxes = $('.tr-checkbox');
    const MAX = 1000;
    $("body").css("cursor", "default");

    $('#id_loader').hide();

    // normal submit action is ignored on a modal form
    $(".modal").on("submit", ".js-form", function () {
        return false;
    });

    // Submit button pressed on a modal form
    $(".modal").on("click", ".js-submit", function () {
        let form = $(this).closest("form");
        let submitter = $(this).attr("name");
        ajax_submit(form, submitter);
        return false;
    });

    // submit on a non-modal form
    $(".js-submit").click(function () {
        let form = $(this).closest("form");
        let submitter = $(this).attr("name");
        ajax_submit(form, submitter);
        return false;
    });

    function ajax_submit(form, submitter) {
        let data = form.serialize() + '&' + encodeURIComponent(submitter) + '=';
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.valid) {
                    $(data.modal_id).modal("hide");
                    if (data.return_url) {
                        ajax_get("", data.return_url)
                    } else {
                        location.reload(true)
                    }
                } else {
                    $(data.modal_id).modal("show");
                    $(data.modal_id + " .modal-content").html(data.html_form);
                }
            },
            error: function(e) {
                console.log(e);
            }
        });
        return false;
    }

    // Button clicked on a modal form. Load a new modal form, passing the current url as the return path
    $(".modal").on("click", ".js-call", function () {
        let url = $(this).prop("name").replace("/0/", "/");
        call_modal(url, last_path)
    });

    // Call from non-modal - don't pass a return address
    $(".js-call").click(function () {
        let url = $(this).prop("name").replace("/0/", "/");
        call_modal(url, "")
    });

    function call_modal(call_url, return_url) {
        $.ajax({
            url: call_url,
            type: 'get',
            dataType: 'json',
            data: {return_url: return_url},
            success: function (data) {
                console.log(data)
                $(data.modal_id).modal("show");
                $(data.modal_id + " .modal-content").html(data.html_form);
            },
            error: function(e) {
                console.log(e);
            }
        });
    }


    // Request and show the modal create form
    $(".js-create").click(function () {
        $.ajax({
            url: 'create/',
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $("#modal-form").modal("show");
            },
            success: function (data) {
                $("#modal-form .modal-content").html(data.html_form);
            }
        });
    });

    // called by update form to delete record
    $(".js-delete").click(function () {
        let pk = $('#pk').val();
        $.ajax({
            url: 'update/' + pk + '/',
            data: 'delete',
            type: 'post',
            dataType: 'json',
            success: function () {
                $("#modal-form").modal("hide");
                location.reload(true)
            }
        });
    });


    // called by table click to load update form
    function ajax_get(pk, action) {
        if (pk) {
            action = action + '/' + pk + '/';
        }
        $.ajax({
            url: action,
            type: 'get',
            dataType: 'json',
            success: function (data) {
                $("#modal-form").children().addClass(data.modal_class);
                $("#modal-form .modal-content").html(data.html_form);
                $("#modal-form").modal("show");
                last_path = data.path;
            }
        });
    }

    if ($('#select_all').prop('checked')) {
        select_all(true);
    } else {
        countChecked();
        highlight_array(chkboxes);
    }

    $('#select_all_page').click(function () {
        $('#select_all').prop("checked", false)
        for (var i = 0; i < chkboxes.length; i++) {
            chkboxes[i].checked = this.checked;
            highlight(chkboxes[i]);
        }
        countChecked();
        lastChecked = null;
    });

    $('#select_all').click(function () {
        select_all(this.checked);
    });

    $('.table').click(function (e) {
        if (e.target.className === 'tr-checkbox') {
            let chkbox = e.target;
            highlight(chkbox);
            if (!lastChecked) {
                lastChecked = chkbox;
            } else if (e.shiftKey) {
                let start = chkboxes.index(chkbox);
                let end = chkboxes.index(lastChecked);
                let subset = chkboxes.slice(Math.min(start, end), Math.max(start, end) + 1);
                subset.prop('checked', chkbox.checked);
                highlight_array(subset);
                lastChecked = chkbox;
            } else {
                lastChecked = chkbox;
            }
            countChecked();
        } else if (e.target.tagName === 'TD') {
            // redirect when click on row
            if (typeof e.target.parentNode.dataset.url !== 'undefined') {
                window.document.location = e.target.parentNode.dataset.url;
            }
            // ajax get when click on row
            if (typeof e.target.parentNode.dataset.pk !== 'undefined') {
                let pk = e.target.parentNode.dataset.pk;
                if (document.getElementById("allow_update")) {
                    ajax_get(pk, "update")
                } else if (document.getElementById("allow_detail")) {
                    ajax_get(pk, "detail")
                }
            }
        }
    });

    function highlight_array(boxes) {
        for (var i = 0; i < boxes.length; i++) {
            highlight(boxes[i]);
        }
    }

    function highlight(box) {
        let node = $(box).closest('.table-row')[0];
        if (box.checked) {
            $(node).addClass('table-info');
        } else {
            $(node).removeClass('table-info');
        }
    }

    function select_all(state) {
        $('#select_all_page').prop("checked", false);
        for (var i = 0; i < chkboxes.length; i++) {
            chkboxes[i].checked = state;
            chkboxes[i].disabled = state;
            highlight(chkboxes[i]);
        }
        if (state) {
            $('#count').text('All');
            $('#selected').addClass('table-info')
        } else {
            $('#count').text('0');
            $('#selected').removeClass('table-info');
        }
        $('#dropdownMenu').prop('disabled', !state);
        lastChecked = null;
    }

// Count the number of checked rows
    function countChecked() {
        let count = document.querySelectorAll('.tr-checkbox:checked').length;
        let goDisabled = ((count === 0) || (count > MAX));
        if (count > MAX) {
            count = "Maximum is {MAX}";
        }
        $('#count').text(count);
        $('#dropdownMenu').prop('disabled', goDisabled);
    }

    // ---------- Filtering code -------

    // changed filter auto submits the form
    $(".form-control").change(function () {
        if ($(this).parent().hasClass("auto-submit")) {
            doFilter();
        }
    });

    // blur catches datepicker changes
    $(".form-control").blur(function () {
        if ($(this).parent().parent().hasClass("auto-submit")) {
            doFilter();
        }
    });

    let ready = false;
    $("#lines_per_page").val($("#id_per_page").val());
    ready = true;

    $("#lines_per_page").change(function () {
        if (ready) {
            $("#id_per_page").val($("#lines_per_page").val());
            doFilter();
        }
    });

    $('#id_filter').click(doFilter);

    function doFilter() {
        $('#id_loader').show();
        $('#id_table_data').hide();
        $("body").css("cursor", "progress");
        $('#id_filter_form').submit();
    }
});

function margin_calc() {
    let margin = 0
    let min_margin = 0
    let cost = int_or_zero("id_cost_price");
    let restoration = int_or_zero("id_restoration_cost");
    let sale = int_or_zero('id_sale_price');
    let min_sale = int_or_zero('id_minimum_price');
    let total_cost = cost + restoration;
    let profit = sale - total_cost;
    let min_profit = min_sale - total_cost;
    if (profit > 0 && sale > 0) {
        margin = parseInt(profit / sale * 1000) / 10;
    }
    if (min_profit > 0 && min_sale > 0) {
        min_margin = parseInt(min_profit / min_sale * 1000) / 10;
    }
    $('#id_restoration_cost').val(restoration / 100);
    $('#id_sale_price').val(sale / 100);
    $('#id_minimum_price').val(min_sale / 100);
    $("#id_total_cost").html("£" + total_cost / 100);
    $('#id_margin').html(margin + "%");
    $('#id_min_margin').html(min_margin + "%");
}

function int_or_zero(id) {
    let v = document.getElementById(id).value;
    if (typeof v !== 'undefined') {
        let x = parseInt(v);
        if (isNaN(x)) {
            return 0;
        } else {
            return x * 100;
        }
    }
}


