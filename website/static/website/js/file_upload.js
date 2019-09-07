// code to handle file upload
function bs_input_file() {
    $(".input-file").before(
        function () {
            if (!$(this).prev().hasClass('input-ghost')) {
                var element = $("<input type='file' class='input-ghost' style='visibility:hidden; height:0'>");
                element.attr("name", $(this).attr("name"));
                element.change(function () {
                    element.next(element).find('input').val((element.val()).split('\\').pop());
                    $('#idUpload').removeAttr('disabled');
                });
                $(this).find("button.btn-choose").click(function () {
                    element.click();
                });
                $(this).find("button.btn-reset").click(function () {
                    element.val(null);
                    $('#idUpload').attr('disabled', 'disabled');
                    $(this).parents(".input-file").find('input').val('');
                });
                $(this).find('input').css("cursor", "pointer");
                $(this).find('input').mousedown(function () {
                    $(this).parents('.input-file').prev().click();
                    return false;
                });
                return element;
            }
        }
    );
}

$(function () {
    bs_input_file();
});


$('#idForm').submit(function (e) {
    e.preventDefault();
    $form = $(this)
    var formData = new FormData(this);
    $.ajax({
        url: window.location.pathname,
        type: 'POST',
        data: formData,
        success: function (response) {
            console.log('POST response received')
            if (response['success']){
                location.reload(true)
            }
        },
        cache: false,
        contentType: false,
        processData: false
    });
});