// Code to work with jqTree used by category_detail.html
(function () {
  $('#tree').tree({
    autoOpen: true,
    autoEscape: false,
    dragAndDrop: true,
    onCanMoveTo:
      function (moved_node, target_node, position) {
        if (position == 'after') {
          return true;
        } else if (position == 'inside') {
          if (target_node.items == 0) {
            return true;
          }
        }
      }
  }).on(
    'tree.move',
    function (event) {
      event.preventDefault();
      // do the move first, and _then_ POST back.
      event.move_info.do_move();
      let data = {
        'node': event.move_info.moved_node.id,
        'target': event.move_info.target_node.id,
        'position': event.move_info.position,
        'previous': event.move_info.previous_parent.id,
        'children': child_ids(event.move_info.target_node)
      }
      $.post('', data);
    }
  );

  function child_ids(node) {
    let result = [];
    for (let i = 0; i < node.children.length; i++) {
      result.push(node.children[i].id);
    }
    return result
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        let cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

// from django documentation
  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    }
  });
})
();