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

    // .js-submit validates form
    $(".modal").on("click", ".js-submit", function () {
        ajax_post(this, true);
        return false;
    });

    // .js-post has no validation and pops return by default
    $(".modal").on("click", ".js-post", function () {
        ajax_post(this, false);
        return false;
    });


// Button clicked on a modal form. Load a new modal form, passing the current url as the return path
    $(".modal").on("click", ".js-link", function () {
        ajax_get(this.href, last_path);
        return false;
    });

    // Button clicked on a modal form. Load a new modal form, passing the current url as the return path
    $(".modal").on("click", ".js-href", function () {
        ajax_get(this.href, last_path);
        return false;
    });


    // .js-submit on a non-modal form
    $(".js-submit").click(function () {
        ajax_post(this, true);
        return false;
    });


// Call from an <a> tag, target is in href
    $(".js-href").click(function () {
        ajax_get(this.href, last_path);
        return false;
    });

    $(".js-link").click(function () {
        ajax_get(this.href, last_path);
        return false;
    });

// Request and show the modal create form
    $(".js-create").click(function () {
        ajax_get('create/', "");
        return false;
    });

// called by table click on a row to load update form
    function ajax_table_get(pk, url) {
        if (pk) {
            url = url + '/' + pk + '/';
        }
        ajax_get(url, "");
    }

    function ajax_get(call_url, return_url, no_push = false) {
        $.ajax({
            url: call_url,
            type: 'get',
            dataType: 'json',
            data: {
                return_url: return_url,
                no_push: no_push
            },
            success: function (data) {
                process_get(data);
            },
            error: function (e) {
                console.log(e);
            },
            timeout: 10000
        });
    }

    function process_get(data) {
        // console.log(data);
        $(data.target_id).html(data.html);
        if (data.html.includes('modal-dialog')) {
            $(data.target_id).modal("show");
        }
        if (data.html.includes('fp_config')) {
            flatpickrInit();
        }
        last_path = data.path;
    }

    function ajax_post(button, validate) {
        let form = $(button).closest("form");
        let target_id = $(button).attr('target_id');
        let no_return = $(button).attr('no_return');
        let data = `${form.serialize()}&${encodeURIComponent(button.name)}=&x_validate=${validate}&x_target_id=${target_id ? target_id : ""}&x_no_return=${no_return}`;
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.form_invalid || data.error) {
                    process_get(data);
                } else {
                    process_post(data);
                }
            },
            error: function (e) {
                console.log(e);
            },
            timeout: 10000
        });
        return false;
    }

    function process_post(data) {
        $(".flatpickr-calendar").remove();
        if (data.next_url) {
            if (data.is_ajax) {
                ajax_get(data.next_url, last_path, true);
            } else {
                if ($(data.target_id).html().includes("modal-dialog")) {
                    $(data.target_id).modal("hide");
                }
                window.location.href = data.next_url;
            }
        } else {
            window.location.reload();
        }
    }


// called by update form to delete record
    $(".js-delete").click(function () {
        let pk = $('#pk').val();
        $.ajax({
            url: 'update/' + pk + '/',
            data: 'delete',
            type: 'post',
            dataType: 'json',
            success: function () {
                process_post(data);
            }
        });
    });


    if ($('#select_all').prop('checked')) {
        select_all(true);
    } else {
        countChecked();
        highlight_array(chkboxes);
    }


    $('#select_all_page').click(function () {
        $('#select_all').prop("checked", false);
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
                if (document.getElementById("ajax_update")) {
                    ajax_table_get(pk, "update");
                } else if (document.getElementById("ajax_detail")) {
                    ajax_table_get(pk, "detail");
                } else if (document.getElementById("detail")) {
                    window.document.location = e.target.parentNode.dataset.url;
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

    $(".checkbox").change(function () {
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
    $("#hidden_per_page").val($("#id_per_page").val());
    ready = true;

    $("#id_per_page").change(function () {
       if (ready) {
            $("#hidden_per_page").val($("#id_per_page").val());
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


// flatpickr initialisation placed here so works for date field loaded in a modal.

    function flatpickrInit() {
        let flatpickr_db = {}, linked_configs = [];
        document.querySelectorAll('[fp_config]:not([disabled])').forEach(function (inputElement) {
            try {
                var config = JSON.parse(inputElement.getAttribute('fp_config'));
            } catch (x) {
            }
            if (config.id && config.options) {
                let inputWrapper;
                if (config.options.wrap) {
                    inputElement.setAttribute('data-input', '');
                    inputWrapper = inputElement.closest('.flatpickr-wrapper');
                    if (!inputWrapper) {
                        throw new Error(
                            'django-flatpickr error:: When wrap option is set to true, ' +
                            'flatpickr input element should be contained by ".flatpickr-wrapper" element'
                        )
                    }
                }
                if (config.linked_to) linked_configs.push(config);
                flatpickr_db[config.id] = {
                    config: config,
                    instance: flatpickr(inputWrapper || inputElement, config.options)
                }
            }
        });
        linked_configs.forEach(function (config) {
            let flatpickr_from_instance = flatpickr_db[config.linked_to].instance;
            let flatpickr_to_instance = flatpickr_db[config.id].instance;
            flatpickrOnChange(flatpickr_from_instance, function (selectedDates) {
                flatpickr_to_instance.set('minDate', selectedDates[0] || false);
            });
            flatpickrOnChange(flatpickr_to_instance, function (selectedDates) {
                flatpickr_from_instance.set('maxDate', selectedDates[0] || false);
            });
        });

        function flatpickrOnChange(instance, callbackFn) {
            /* This prevents the infinite loop */
            function resolveTime(selectedDates) {
                return selectedDates.length ? selectedDates[0].getTime() : 0;
            }

            let rememberedTime = resolveTime(instance.selectedDates);
            callbackFn(instance.selectedDates, true);
            instance.set('onChange', function (selectedDates) {
                let selectedTime = resolveTime(selectedDates);
                if (selectedTime != rememberedTime) {
                    rememberedTime = selectedTime;
                    callbackFn(selectedDates);
                }
            });
        }
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


