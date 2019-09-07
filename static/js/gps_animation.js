
var map;
function initMap() {

  // MTMLから、地図を表示したいcanvas要素を取得する
  var canvas = document.getElementById('map_canvas');

  // map中心の座標
  var latlng = {
    lat: 35.297058,
    lng: 139.5523478
  };

  // 中心地点の指定と、マップの拡大具合
  var map_options = {
    center: latlng,
    zoom: 15
  }

  // goole mapを表示
  map = new google.maps.Map(canvas,map_options);

  // マーカー表示する
  marker = new google.maps.Marker({
    position: latlng,
    map: map
  });
}
