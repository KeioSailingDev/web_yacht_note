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
  for(var yacht_index = 1; yacht_index < 8; yacht_index++){

    var show_yacht_index = yacht_index - 1;

    //艇番select要素のidを生成
    var yacht_id = 'yachtnumber' + yacht_index;

    //艇番select要素のオブジェクトを取得
    var target_yacht = document.getElementById(yacht_id);

    //各select要素で選択されている値を取得
    var target_yacht_value = target_yacht.value;

    //リストの値が「未入力」の場合は、以降のリストを非表示にする
    if(target_yacht_value == ""){
      $('.yacht-skipper:gt('+show_yacht_index+')').hide();
      var hidden_yacht = yacht_index + 1
      break;
    }
  };

  $('#open-yacht-skipper').click(function(){
    $('.yacht-skipper:lt('+hidden_yacht+')').show();
    hidden_yacht += 1;
  });

});
