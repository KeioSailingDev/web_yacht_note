// マップ初期化
function initialize() {
  // 表示する場所のidを取得
  var target = document.getElementById("map_canvas")
  // 経度：lat，緯度：lngを設定
  var latlng = {lat: 35.383575, lng: 139.344170};
  var options = {
    zoom: 10, // ズーム1は一番小さい
    center: latlng //Mapの中央:上の座標
  };
  // Mapを作成
  map = new google.maps.Map(target, options);

  // マーカーを表示
  var marker = new google.maps.Marker({
    position: latlng,
    map: map,
    title: 'where' // マーカーの名前
  });

  // Mapをクリックする時の動作
  map.addListener("click",function(e){
    // コンソールで経度を表示
    console.log("lat: " + e.latLng.lat());
    // コンソールで緯度を表示
    console.log("lng: " + e.latLng.lng());
    // コンソールで{経度,緯度}を表示
    console.log("(lat,lng): " + e.latLng.toString());
    // this.setCenter(e.latLng); // クリックする場所をMapの中心にする(画面の移動速度が速い)
    this.panTo(e.latLng); //クリックする場所をMapの中心にする(画面の移動速度がゆっくり)
    // クリックする場所をマーカーを立てる
    var click_marker = new google.maps.Marker({
      position: e.latLng,
      map: map,
      title: e.latLng.toString(),
      animation: google.maps.Animation.DROP // マーカーを立つときのアニメーション
    });
    // 上で立てたマーカーをもう一度クリックするとマーカーを削除
    click_marker.addListener("click",function(){
      this.setMap(null);
    });
  });
}

// // 「マーカー作成」ボタンをクリックする時のマーカー表示
// // JSONデータを使って座標と名称を記録
// function loadJson(){
//   var json = [];
//   $(function(){
//     // JSONのファイルを読み込む
//     $.getJSON("data.json", function(data) {
//       json = data;
//       //JSONの要素数分マーカーを作成
//       console.log(json);
//       for (i = 0; i < json.length; i++) {
//         latlng = new google.maps.LatLng(json[i].lat,  json[i].lng);
//         var marker = new google.maps.Marker({
//             position: latlng,
//             map: map,
//         });
//       }
//     });
//   });
// }
