// Handle checkboxes in tables, and modal forms
$(document).ready(function () {
    'use strict';
    let lastChecked = null;
    let chkboxes = $('.tr-checkbox');
    const MAX = 1000;
    $("body").css("cursor", "default");

    $('#id_loader').hide();
    // set clicked attr on button that submitted the form

    $("#modal-form").on("click", ".js-submit", function () {
        let form = $(this).parents("form");
        let submitter = $(this).attr("name");
        submit(form, submitter);
        return false;
    });

    function submit(form, submitter) {
        let data = form.serialize();
        data += '&' + encodeURIComponent(submitter) + '=';
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.valid) {
                    $("#modal-form").modal("hide");
                    if (data.return_url) {
                        ajax_get("", data.return_url)
                    } else {
                        location.reload(true)
                    }
                } else {
                    $("#modal-form").modal("show");
                    $("#modal-form .modal-content").html(data.html_form);
                }
            }
        });
        return false;
    }

    // request and show the modal create form
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

    // changed filter auto submits the form
    $(".form-control").change(function() {
        if ($(this).parent().hasClass("auto-submit")){
            doFilter();
            //$(this).closest("form").submit();
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

    // normal submit button is ignored
    $("#modal-form").on("submit", ".js-form", function () {
        return false;
    });

    // called by table click to load update form
    function ajax_get(pk, action) {
        if(pk){
            action = action + '/' + pk + '/';
        }
        $.ajax({
            url: action,
            type: 'get',
            dataType: 'json',
            success: function (data) {
                $("#modal-form").modal("show");
                $("#modal-form .modal-content").html(data.html_form);
                $("#return_url").val(data.return_url);
            }
        });
    }

    if ($('#select_all').prop('checked')) {
        select_all(true);
    } else {
        countChecked();
        highlight_array(chkboxes);
    }

    $('#id_filter').click(doFilter);

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

    function doFilter() {
        $('#id_loader').show();
        $('#id_table_data').hide();
        $("body").css("cursor", "progress");
        $('#id_filter_form').submit();
    }
})
;