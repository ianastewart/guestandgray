var urls = JSON.parse(document.getElementById('id_urls').textContent);
$(document).ready(function () {
    wrap_typeahead('#select_contact', urls['lookup'], '', gotContact);
    $('#id_contact_name').prop("disabled", true);

    // user selected a contact
    function gotContact(data) {
        $('#contact').val(data.id);
        $('#details').html(data.html);
        $('.submit-btn').prop("disabled", false)
        $("#newRadio").prop("checked", false);
        $("#searchRadio").prop("checked", false);
        $('#searchGroup').hide();
    }

    // enable the search form
    $("#searchRadio").click(function () {
        $('#searchGroup').show();
        $('.submit-btn').prop("disabled", true);
        $('#contact').html("");
        $('#select_contact').val("").prop("disabled", false).css('background-color', '#ffffff').focus();
    });

    // request and show the modal form to create a contact
    $("#newRadio").click(function () {
        $.ajax({
            url: urls['create'],
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $('#searchGroup').hide()
                $('#btn_next').prop("disabled", true)
                $('#contact').html("");
                $("#modal-form").modal("show");
            },
            success: function (data) {
                $("#modal-form .modal-content").html(data.html_form);
            }
        });
    })

        // normal submit action is ignored on a modal form
    $(".modal").on("submit", ".js-form", function () {
        return false;
    });

    $("#modal-form").on("click", ".js-submit", function () {
        var form = $(this).parents("form");
        var submitter = $(this).attr("name");
        let data = form.serialize() + '&' + encodeURIComponent(submitter) + '=';
        data += '&' + encodeURIComponent(submitter) + '=';
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                $("#modal-form .modal-content").html(data.html_form);
                if (data.valid) {
                    $("#modal-form").modal("hide");
                    $.ajax({
                        url: urls["lookup"],
                        data: {'term': 'pk=' + data.pk},
                        success: function (reply) {
                            gotContact(reply[0]);
                        }
                    })
                } else {
                    $("#modal-form").modal("show");
                }
            }
        });
        return false;
    });
});
