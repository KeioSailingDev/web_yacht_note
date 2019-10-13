$(function() {
    // Setup leaflet map
    var map = new L.Map('map');

    // map layer
    var basemapLayer = new  L.tileLayer('https://tile.thunderforest.com/transport-dark/{z}/{x}/{y}.png?apikey=0da2c2964ad240698fb6f3f16eec226b', {
        attribution: '&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        apikey: '0da2c2964ad240698fb6f3f16eec226b',
        maxZoom: 22
    }).addTo(map);

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

    // =====example3.jsからの引用=====
    // var shipIcon = L.icon({
    //                         iconUrl: '../img/boat/boat-01.png',
    //                         iconSize: [7, 20], // size of the icon
    //                         // shadowSize: [0, 0], // size of the shadow
    //                         iconAnchor: [3.5, 10], // point of the icon which will correspond to marker's location
    //                         // shadowAnchor: [0, 0], // the same for the shadow
    //                         popupAnchor: [0, -10] // point from which the popup should open relative to the iconAnchor
    //                     });

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

        // =====元であるexapmle2のもの=====
        marker: function(){
            return {
                icon: L.AwesomeMarkers.icon({
                    prefix: 'fa',
                    icon: 'bullseye',
                    markerColor: _assignColor()
                })
            };
        }

    // =====example3に合わせてみたVer=====
    //     marker: function(){
    //         return {
    //             icon: L.AwesomeMarkers.icon({
    //                 icon: shipIcon,
    //             })
    //         };
    //     }
    

    };

    // Initialize playback
    var playback = new L.Playback(map, demoTracks, null, playbackOptions);

    // Initialize custom control
    var control = new L.Playback.Control(playback);
    control.addTo(map);

    // Add data
    playback.addData(blueMountain);

});
