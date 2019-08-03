var map;
function initMap() {
  map = new google.maps.Map(document.getElementById('map_canvas'), {
    center: {lat: 35.284470, lng: 139.565830},
    zoom: 15
  });
}
