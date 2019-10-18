// Handle checkboxes in tables, and modal forms
$(document).ready(function () {
    'use strict';
    var lastChecked = null;
    var chkboxes = $('.tr-checkbox');
    var MAX = 1000;
    $("body").css("cursor", "default");

    // set clicked attr on button that submitted the form
    $("#modal-form").on("click", ".js-submit", function () {
        console.log("js-submit")
        var form = $(this).parents("form");
        var submitter = $(this).attr("name")
        submit(form, submitter)
    });

    function submit(form, submitter){
        var data = form.serialize();
        data += '&' + encodeURIComponent(submitter) + '=';
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.valid) {
                    $("#modal-form").modal("hide");
                    if (data.url) {
                        location.replace(data.url);
                    } else {
                        location.reload(true)
                    }
                } else {
                    $("#modal-form .modal-content").html(data.html_form);
                }
            }
        });
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
    })

    // called by update form to delete record
    $(".js-delete").click(function () {
        var pk = $('#pk').val();
        $.ajax({
            url: 'update/' + pk + '/',
            data: 'delete',
            type: 'post',
            dataType: 'json',
            success: function (data) {
                $("#modal-form").modal("hide");
                location.reload(true)
            }
        });
    })

    // normal submit button is ignored
    $("#modal-form").on("submit", ".js-form", function () {
        console.log("ignore submit")
        return false;
    });

    // called by table click to load update form
    function ajax_update(pk) {
        $.ajax({
            url: 'update/' + pk + '/',
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $("#modal-form").modal("show");
            },
            success: function (data) {
                $("#modal-form .modal-content").html(data.html_form);
            }
        });
    }

    if ($('#select_all').prop('checked')) {
        select_all(true);
    } else {
        countChecked();
        highlight_array(chkboxes);
    }

    $('#id_search').click(doSearch);

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
            var chkbox = e.target;
            highlight(chkbox);
            if (!lastChecked) {
                lastChecked = chkbox;
            } else if (e.shiftKey) {
                var start = chkboxes.index(chkbox);
                var end = chkboxes.index(lastChecked);
                var subset = chkboxes.slice(Math.min(start, end), Math.max(start, end) + 1);
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
            // ajax update form when click on row
            if (document.getElementById("allow_update")) {
                if (typeof e.target.parentNode.dataset.pk !== 'undefined') {
                    ajax_update(e.target.parentNode.dataset.pk)
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
        var node = $(box).closest('.table-row')[0];
        if (box.checked) {
            $(node).addClass('table-info');
        } else {
            $(node).removeClass('table-info');
        }
    }

    function select_all(state) {
        $('#select_all_page').prop("checked", false)
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
        var count = document.querySelectorAll('.tr-checkbox:checked').length;
        var goDisabled = ((count === 0) || (count > MAX));
        if (count > MAX) {
            count = "Maximum is {MAX}";
        }
        $('#count').text(count);
        $('#dropdownMenu').prop('disabled', goDisabled);
    }

    function doSearch() {
        $('#id_loader').show();
        $('#table_tile').hide();
        $('#search_form').submit();
        $("html").addClass("wait");
    }
})
;