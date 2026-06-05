$("#category_search").click(function () {
  var ref = document.getElementById("id_category_ref").value;
  var target_id = "#id_category_image";
  var error_id = "#id_category_error"
  ajax_get(ref, target_id, error_id);
})

$("#archive_search").click(function () {
  var ref = document.getElementById("id_archive_ref").value;
  var target_id = "#id_archive_image";
  var error_id = "#id_archive_error";
  ajax_get(ref, target_id, error_id);
})

function ajax_get(ref, target_id, error_id) {
  $.ajax({
    url: document.getElementById("images_url").innerText,
    type: 'get',
    dataType: 'json',
    data: {
      ref: ref,
      target: target_id
    },
    success: function (data) {
      if (data.image) {
        var d = new Date();
        $(error_id).text("");
        $(target_id).attr("src", data.image + "?" + d.getMilliseconds());
      } else if (data.error) {
        $(error_id).text(data.error);
      }
    },
    error: function (e) {
      $(error_id).text("Error");
    },
    timeout: 10000
  });
}