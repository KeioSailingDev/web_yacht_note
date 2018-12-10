// show_outline.html内の、練習メニューの表示
$(function(){

  for(var list_num = 2; list_num < 16; list_num++){

    //リストのインデックス番号を取得
    var list_index = list_num - 2

    //リストのidを生成
    var list_id = 'training' + list_num;

    //リストオブジェクトを取得
    var target_list = document.getElementById(list_id);

    //各リストで選択されている値を取得
    var target_list_value = target_list.value;

    //リストの値が「未入力」の場合は、以降のリストを非表示にする
    if(target_list_value == ""){
      $('#menu > li:gt('+list_index+')').hide();
      var hidden_list = list_num
      console.log(hidden_list)
      break;
    }

  };

  $('#menu-open').click(function(){

    $('#menu > li:lt('+hidden_list+')').show();

    hidden_list += 1;

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
