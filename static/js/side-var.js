$(document).ready(function () {
  $('#sidr-left-top-button').sidr({
    name: 'sidr-left-top',
    speed: 500,
    timing: 'ease-in-out',
    source: 'sidr-left-top'
  });
  $('#sidr-right-top-button').sidr({
    name: 'sidr-right-top',
    speed: 500,
    side: 'right',
    source: 'sidr-right-top'
  });
});

$( window ).resize(function () {
  $.sidr('close', 'sidr-left-top');
  $.sidr('close', 'sidr-right-top');
});


function loading(){
    $("#loading").show();
    // $("#content").hide();
    $("#loading").fadeOut(10000);
    // $("#content").fadeIn(50000);
}
