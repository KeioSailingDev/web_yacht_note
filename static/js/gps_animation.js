// var map;
// function initMap() {
//   var latlng = {
//     lat: 35.297058,
//     lng: 139.5523478
//   },
//   map = new google.maps.Map(document.getElementById('map_canvas'), {
//     center: latlng,
//     zoom: 15
//   });
//   // 地図上にマーカー表示する
//   marker = new google.maps.Marker({
//     position: latlng,
//     map: map
// });
// }



var map;
function initMap() {

  // MTMLから、地図を表示したいcanvas要素を取得する
  var canvas = document.getElementById('map_canvas');

  var latlng = {
    lat: 35.297058,
    lng: 139.5523478
  };

  var map_options = {
    center: latlng,
    zoom: 15
  }

  map = new google.maps.Map(canvas,map_options);
  // 地図上にマーカー表示する
  marker = new google.maps.Marker({
    position: latlng,
    map: map
  });
}
