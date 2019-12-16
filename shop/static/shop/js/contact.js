var urls = JSON.parse(document.getElementById('id_urls').textContent);
$(document).ready(function () {
    wrap_typeahead('#select_contact', urls['lookup'], '', gotContact);
    if ($('#details').text() !== ""){
        setDetails();
    }

    // user selected a contact
    function gotContact(data) {
        $('#id_contact_id').val(data.id);
        setDetails();
        $('#details').html(data.html);
        $("#newRadio").prop("checked", false);
        $("#searchRadio").prop("checked", false);
        $('#searchGroup').hide();
    }

    function clearDetails() {
        $('#detailsCard').removeClass('bg-white');
        $('#detailsCard').addClass('bg-light');
        $('#details').html("");
        $('.submit-btn').prop("disabled", true);
    }

    function setDetails() {
        $('#detailsCard').removeClass('bg-light');
        $('#detailsCard').addClass('bg-white');
         $('.submit-btn').prop("disabled", false);
    }

    // enable the search form
    $("#searchRadio").click(function () {
        clearDetails();
        $('#searchGroup').show();
    });

    // request and show the modal form to create a contact
    $("#newRadio").click(function () {
        $.ajax({
            url: urls['create'],
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                clearDetails();
                $('#searchGroup').hide()
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
