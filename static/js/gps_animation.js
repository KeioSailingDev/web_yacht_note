$(function() {
    // Setup leaflet map
    var map = new L.Map('map');

    var basemapLayer = new L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png?{foo}', {foo: 'bar', attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'}).addTo(map);

    // Center map and default zoom level
    map.setView([44.61131534, -123.4726739], 9);

    // Adds the background layer to the map
    map.addLayer(basemapLayer);

    // Colors for AwesomeMarkers
    var _colorIdx = 0,
        _colors = [
          'orange',
          'green',
          'blue',
          'purple',
          'darkred',
          'cadetblue',
          'red',
          'darkgreen',
          'darkblue',
          'darkpurple'
        ];

    function _assignColor() {
        return _colors[_colorIdx++%10];
    }

    // =====================================================
    // =============== Playback ============================
    // =====================================================

    // Playback options
    var playbackOptions = {
        // layer and marker options
        layer: {
            pointToLayer : function(featureData, latlng){
                var result = {};

                if (featureData && featureData.properties && featureData.properties.path_options){
                    result = featureData.properties.path_options;
                }

                if (!result.radius){
                    result.radius = 5;
                }

                return new L.CircleMarker(latlng, result);
            }
        },

        marker: function(){
            return {
                icon: L.AwesomeMarkers.icon({
                    prefix: 'fa',
                    icon: 'bullseye',
                    markerColor: _assignColor()
                })
            };
        }
    };

    // Initialize playback
    var playback = new L.Playback(map, demoTracks, null, playbackOptions);

    // Initialize custom control
    var control = new L.Playback.Control(playback);
    control.addTo(map);

    // Add data
    playback.addData(blueMountain);

});
