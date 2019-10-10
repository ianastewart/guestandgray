// Handle checkboxes in tables to select rows
$(document).ready(function () {
    'use strict';
    var lastChecked = null;
    var chkboxes = $('.tr-checkbox');
    var MAX = 1000;

    $("body").css("cursor", "default");

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

    $(".js-delete").click(function () {
        var pk = $('#pk').val();
        $.ajax({
            url: 'update/'+pk+'/',
            data: 'delete',
            type: 'post',
            dataType: 'json',
            success: function (data) {
                $("#modal-form").modal("hide");
                location.reload(true)
            }
        });
    })

    $("#modal-form").on("submit", ".js-form", function () {
        var form = $(this);
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.valid) {
                    $("#modal-form").modal("hide");
                    location.reload(true)
                } else {
                    $("#modal-form .modal-content").html(data.html_form);
                }
            }
        });
        return false;
    });

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
            if (typeof e.target.parentNode.dataset.url !== 'undefined') {
                window.document.location = e.target.parentNode.dataset.url;
            }
            if (typeof e.target.parentNode.dataset.pk !== 'undefined') {
                ajax_update(e.target.parentNode.dataset.pk)
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
});