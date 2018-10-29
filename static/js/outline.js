$(function(){

  $('#menu > li:gt(0)').hide();

  var Num = 0;

  $('#menu-open').click(function(){

    Num += 1;

    $('#menu > li:lt('+Num+')').show();

  });

});
