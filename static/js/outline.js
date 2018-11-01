// show_outline.html内の、練習メニューの表示
$(function(){

  $('#menu > li:gt(0)').hide();

  var Menu_Num = 0;

  $('#menu-open').click(function(){

    Menu_Num += 1;

    $('#menu > li:lt('+Menu_Num+')').show();

  });

});

//艇番-デバイス-スキッパー-クルーの一組を表示
$(function(){
  $('.yacht-skipper:gt(0)').hide();

  var Yacht_Num = 0;

  $('#open-yacht-skipper').click(function(){

    Yacht_Num += 1;

    $('.yacht-skipper:lt('+Yacht_Num+')').show();

  });

});
