// code to handle image file management

$(function () {
  bs_input_file();

  $(".js-action").click(function () {
    var form = $("#action-form");
    var dataset = $(this)[0].dataset;
    $('#idAction').val(dataset.action);
    $('#idId').val(dataset.id);
    $.ajax({
      url: window.location.pathname,
      type: form.attr("method"),
      data: form.serialize(),
      success: function (data) {
        location.reload(true);
      }
    });
    return false;
  });
});


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
          $('#idFeedback').text('')
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


$('#idForm').submit(function (e) {
  e.preventDefault();
  $form = $(this)
  var formData = new FormData(this);
  $.ajax({
    url: window.location.pathname,
    type: 'POST',
    data: formData,
    success: function (response) {
      console.log(response);
      if (response.success) {
        location.reload(true)
      } else {
        $('#idFeedback').text(response.error)
        $('#idUpload').attr('disabled', 'disabled')
      }
    },
    cache: false,
    contentType: false,
    processData: false
  });
});
