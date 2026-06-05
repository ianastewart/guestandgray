  $(document).ready(function(){
/* zoom */
    $('#object_image_gallery .img').each( function() {
      $(this).on('mouseover', function() {
        var zoomImg = $(this).attr('data-img-zoom');

        $(this).children('img').css('display', 'none');
        $(this).css('background-image', 'url('+zoomImg+')');
        $(this).css('background-repeat', 'no-repeat');
      });

      $(this).on('mouseout', function() {

        $(this).children('img').css('display', 'inline-block');
        $(this).css('background-image', 'none');
      });

      $(this).on('click', function() {
        var zoomImg = $(this).attr('data-img-zoom');

        var newWindow = window.open(zoomImg, '_blank');
        if( newWindow ) {
          // opened OK
          newWindow.focus();
        } else {
          // popup blocked
        }
      });

      $(this).on('mousemove', function(e) {
        var topLeftX = $(this).offset().left;
        var topLeftY = $(this).offset().top;

        var posX = ( (e.pageX - topLeftX) / $(this).width() ) * 100;
        var posY = ( (e.pageY - topLeftY) / ($(this).height() + 30) ) * 100;

        $(this).css('background-position', posX+'% '+posY+'%');
      });
    });

  });

  /* object gallery */
  object_image_gallery_show = function( img ) {
    var i = $('#object_image_gallery').find('.img');
    i.css('display', 'none');

    var j = $('#object_image_gallery').find( '.'+img );
    j.css('display', 'block');

    return false;
  };
