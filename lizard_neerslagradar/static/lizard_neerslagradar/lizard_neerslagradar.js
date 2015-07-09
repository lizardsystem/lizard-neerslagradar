// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, map, lizard_neerslagradar */
function setup_movable_dialog() {
    // used by open_popup
    $('body').append('<div id="movable-dialog"><div ' +
                     'id="movable-dialog-content"></div></div>');
    var options = {
        autoOpen: false,
        title: '',
        width: 600,
        height: 250,
        zIndex: 10000,
        close: function (event, ui) {
            // clear contents on close
            $('#movable-dialog-content').empty();
        }
    };

    // make an exception for iPad
    if (isAppleMobile) {
        // dragging on touchscreens isn't practical
        options.draggable = false;
        // resizing neither
        options.resizable = false;
        // make width 90% of the entire window
        options.width = $(window).width() * 0.9;
        // make height 80% of the entire window
        options.height = $(window).height() * 0.8;
    }
    $('#movable-dialog').dialog(options);
}
function flotGraphLoadData($container, response) {
    var data = response.data;
    if (data.length === 0) {
        $container.html('Geen gegevens beschikbaar.');
        return;
    }
    var dataset = data[0]['data']
    var middle = dataset[parseInt(dataset.length/2)][0];
    var defaultOpts = {
        series: {
            points: { show: true, hoverable: true, radius: 1 },
            shadowSize: 0
        },
        yaxis: {
            zoomRange: [false, false],
            panRange: false
        },
        xaxis: {
            mode: "time",
            zoomRange: [1 * MS_MINUTE, 400 * MS_YEAR]
        },
        grid: {
            hoverable: true,
            labelMargin: 15,
            markings: [ { xaxis: { from: middle, to: middle }, color: "#588CA8" }]
        },
        pan: { interactive: false },
        zoom: { interactive: false },
    };
    if (isAppleMobile) {
        // enable touch
        defaultOpts.touch = { pan: 'xy', scale: 'x', autoWidth: false,
            autoHeight: false };
        // disable flot.navigate pan & zoom
        defaultOpts.pan.interactive = false;
        defaultOpts.zoom.interactive = false;
    }

    // set up elements nested in our assigned parent div
    $container.css('position', 'relative');
    // first row
    var $graph_row = $('<div class="flot-graph-row" />')
        .css({
            position: 'absolute',
            left: 0, top: 0, bottom: 48, right: 0
        });
    var $y_label_text_wrapper = $('<div/>')
        .css({
            position: 'absolute',
            bottom: 80,
            width: 20
        });
    var $y_label_text = $('<div class="flot-graph-y-label-text" />')
        .css({
            'white-space': 'nowrap',
            'background-color': '#fff'
        })
        .transform({rotate: '-90deg'})
        .html(response.y_label);
    $y_label_text_wrapper.append($y_label_text);
    var $y_label = $('<span class="flot-graph-y-label" />')
        .css({
            position: 'absolute',
            left: 0, top: 0, bottom: 0, width: 20
        });
    $y_label.append($y_label_text_wrapper);
    $graph_row.append($y_label);
    var $graph = $('<span class="flot-graph-canvas" />')
        .css({
            position: 'absolute',
            left: 20, top: 0, bottom: 0, right: 0
        });
    $graph_row.append($graph);
    $container.append($graph_row);

    // initial plot
    var plot = $.plot($graph, data, defaultOpts);
    bindPanZoomEvents($graph);

    if (!isAppleMobile) {
        function showGraphTooltip(x, y, datapoint) {
            var formatted = moment.utc(datapoint[0]).format('LL h:mm');
            $('<div id="graphtooltip">' + formatted + ': '+ datapoint[1] +
                '</div>').css({
                    'position': 'absolute',
                    'top': y - 25,
                    'left': x + 5,
                    'padding': '0.4em 0.6em',
                    'border-radius': '0.5em',
                    'border': '1px solid #111',
                    'background-color': '#fff',
                    'z-index': 11000
            }).appendTo("body");
        }

        $graph.bind("plothover", function (event, pos, item) {
            if (item) {
                $("#graphtooltip").remove();
                showGraphTooltip(item.pageX, item.pageY, item.datapoint);
            } else {
                $("#graphtooltip").remove();
            }
        });
    }
    return plot;
}
(function () {
    function MyLayer (dt, opacity, bbox) {
        this.dt = dt;
        this.opacity = opacity;
        this.bbox = bbox;
        this.ol_layer = null;
    }

    var CssHideableImageLayer = OpenLayers.Class(OpenLayers.Layer.Image, {
        cssVisibility: true,

        initialize: function (name, url, extent, size, options) {
            OpenLayers.Layer.Image.prototype.initialize.apply(
                this, [name, url, extent, size, options]);
            if (options.cssVisibility === true || options.cssVisibility ===
                false) {
                this.cssVisibility = options.cssVisibility;
            }
            this.events.on({
                'added': this.updateCssVisibility,
                'moveend': this.updateCssVisibility,
                scope: this});
        },

        destroy: function () {
            this.events.un({
                'added': this.updateCssVisibility,
                'moveend': this.updateCssVisibility,
                scope: this});
            OpenLayers.Layer.Image.prototype.destroy.apply(this);
        },

        setCssVisibility: function (visible) {
            this.cssVisibility = visible;
            this.updateCssVisibility();
        },

        updateCssVisibility: function () {
            if (this.div) {
                if (this.cssVisibility) {
                    $(this.div).show();
                }
                else {
                    $(this.div).hide();
                }
            }
        }
    });

    var StaticOverviewMap = OpenLayers.Class(OpenLayers.Control.OverviewMap, {
        staticMap: true,

        initialize: function (options) {
            OpenLayers.Control.OverviewMap.prototype.initialize.apply(this,
                [options]);
            if (options.staticMap === true || options.staticMap === false) {
                this.staticMap = options.staticMap;
            }
        },
        updateOverview: function() {
            var mapRes = this.map.getResolution();
            var targetRes = this.ovmap.getResolution();
            var resRatio = targetRes / mapRes;
            if (resRatio > this.maxRatio) {
                // zoom in overview map
                targetRes = this.minRatio * mapRes;
            } else if (resRatio <= this.minRatio) {
                // zoom out overview map
                targetRes = this.maxRatio * mapRes;
            }
            if (!this.staticMap) {
                var center;
                if (this.ovmap.getProjection() !== this.map.getProjection()) {
                    center = this.map.center.clone();
                    center.transform(this.map.getProjectionObject(),
                                     this.ovmap.getProjectionObject() );
                } else {
                    center = this.map.center;
                }
                this.ovmap.setCenter(center, this.ovmap.getZoomForResolution(
                    targetRes * this.resolutionFactor));
            }
            this.updateRectToMap();
        }
    });

    var interval_ms = 100;
    var cycle_layers_interval = null;
    var current_layer_idx = -1;
    var paused_at_end = false;

    var layers = [];
    var regional_layers = [];

    var full_bbox = new OpenLayers.Bounds(
        lizard_neerslagradar.fixed_image_layer_bbox.split(','));

    var regional_bbox = full_bbox;

    for (var i=0; i < lizard_neerslagradar.animation_datetimes.length; i++) {
        var dt = moment(lizard_neerslagradar.animation_datetimes[i].datetime);
        if (lizard_neerslagradar.user_logged_in) {
            layers.push(new MyLayer(dt, 0.2, full_bbox));
            regional_layers.push(new MyLayer(dt, 0.6, regional_bbox));
        } else {
            layers.push(new MyLayer(dt, 0.6, full_bbox));
        }
    }

    var layers_loading = 0;
    var progress_interval = null;
    var $btn;
    var $slider;
    var $progressbar;

    function set_layer (layer_idx) {
        if (current_layer_idx != layer_idx) {
            // swap out visibility
            if (current_layer_idx != -1) {
                var current_layer = layers[current_layer_idx];
                current_layer.ol_layer.setCssVisibility(false);
                if (lizard_neerslagradar.user_logged_in) {
                    current_layer = regional_layers[current_layer_idx];
                    current_layer.ol_layer.setCssVisibility(false);
                }
            }
            if (layer_idx != -1) {
                var layer = layers[layer_idx];
                layer.ol_layer.setCssVisibility(true);
                if (lizard_neerslagradar.user_logged_in) {
                    layer = regional_layers[layer_idx];
                    if (layer && layer.ol_layer) {
                        layer.ol_layer.setCssVisibility(true);
                    }
                }
            }

            // update with next layer index
            current_layer_idx = layer_idx;

            on_layer_changed();
        }
    }

    function cycle_layers () {
        var current_layer = layers[current_layer_idx];
        var regional_layer;
        if (lizard_neerslagradar.user_logged_in) {
            regional_layer = regional_layers[current_layer_idx];
        }
        // don't swap layers when we're still loading
        if ((!current_layer || !current_layer.ol_layer.loading) &&
        (!paused_at_end) &&
        (!lizard_neerslagradar.user_logged_in || !regional_layer || !regional_layer.ol_layer.loading)) {
            // figure out next layer
            var next_layer_idx = (current_layer_idx >= layers.length - 1) ?
                0 : current_layer_idx + 1;
            if (next_layer_idx === 0) {
              paused_at_end = true;
              window.setTimeout(function(){
                paused_at_end = false;
                set_layer(0);
              }, 1000);
            } else {
              set_layer(next_layer_idx);
            }
        }
    }

    function init_cycle_layers () {
        var init_layer = function (idx, layer) {
            var dt_iso_8601 = moment.utc(layer.dt)
                .format('YYYY-MM-DDTHH:mm:ss');
            var wms_params = {
                SERVICE: 'WMS',
                REQUEST: 'GetMap',
                VERSION: '1.1.1',
                LAYERS: 'radar/5min',
                STYLES: 'radar-5min',
                FORMAT: 'image/png',
                TRANSPARENT: false,
                HEIGHT: 497,
                WIDTH: 525,
                INDEX: 101,
                TIME: dt_iso_8601,
                ZINDEX: 20,
                SRS: 'EPSG:3857',
                BBOX: layer.bbox.toBBOX()
            };
            var wms_url = lizard_neerslagradar.wms_base_url + '?' +
                $.param(wms_params);
            var ol_layer = new CssHideableImageLayer(
                'L' + idx,
                wms_url,
                layer.bbox,
                new OpenLayers.Size(525, 497),
                {
                    isBaseLayer: false,
                    alwaysInRange: true,
                    visibility: true, // keep this, so all layers are preloaded
                                      // in the browser
                    cssVisibility: false, // hide layer again with this custom
                                          // option
                    displayInLayerSwitcher: false,
                    metadata: layer,
                    opacity: layer.opacity,
                    eventListeners: {
                        'loadstart': function () {
                            layers_loading++;
                            on_layer_loading_change();
                        },
                        'loadend': function () {
                            layers_loading--;
                            on_layer_loading_change();
                        }
                    },
                    projection: 'EPSG:3857'
                }
            );
            map.addLayer(ol_layer);
            layer.ol_layer = ol_layer;
        };

        $.each(layers, init_layer);
        if (lizard_neerslagradar.user_logged_in) {
            $.each(regional_layers, init_layer);
        }
    }

    function on_layer_changed () {
        if (current_layer_idx != -1) {
            $slider.slider('value', current_layer_idx);
        }
    }

    function init_slider () {
        $slider = $('#timeslider');
        $slider.slider({
            min: 0,
            max: layers.length - 1,
            change: function (event, ui) {
                var layer = layers[ui.value];
                $("#currentdt").html(layer.dt.format('HH:mm'));
            },
            slide: function (event, ui) {
                stop_if_running();
                set_layer(ui.value);
                // hack: force triggering a change event while sliding
                var slider_data = $slider.data('slider');
                slider_data._trigger('change', event, ui);
            }
        });
    }

    function start () {
        $btn.find('i').removeClass('icon-pause').addClass('icon-play');
        $btn.addClass('active');
        cycle_layers_interval = setInterval(cycle_layers, interval_ms);
    }

    function stop () {
        $btn.find('i').removeClass('icon-play').addClass('icon-pause');
        $btn.removeClass('active');
        clearInterval(cycle_layers_interval);
        cycle_layers_interval = null;
    }

    function stop_if_running () {
        if (is_running()) {
            stop();
        }
    }

    function is_running () {
        return cycle_layers_interval !== null;
    }

    function toggle () {
        if (is_running()) {
            stop();
        }
        else {
            start();
        }
    }

    function init_button () {
        $btn = $('#animate');
        $btn.click(function (e) {
            if (e) {
                e.preventDefault();
            }
            toggle();
        });
    }
    function init_geolocation_button () {
        var button = $('.geolocation-btn');
        button.click(function (e) {
            zoomToGeolocation();
            e.preventDefault();
        });
    }
    function init_progress () {
        $progressbar = $('#progressbar');
    }

    function on_layer_loading_change () {
        if (layers_loading > 0) {
            // 'if' control structure split for clarity
            if (progress_interval === null && is_running()) {
                set_progress(0);
                progress_interval = setInterval(update_progress, 300);
            }
        }
        else {
            if (progress_interval !== null) {
                clearInterval(progress_interval);
                progress_interval = null;
                set_progress(1);
            }
        }
    }

    function update_progress () {
        var num_loading_tiles = 0;
        var num_tiles = 0;
        var ratio;
        // sum numLoadingTiles and total amount of tiles per layer
        $.each(layers, function (idx, layer) {
            if (layer.ol_layer && layer.ol_layer.grid) {
                num_loading_tiles += layer.ol_layer.numLoadingTiles;
                for (var i=0; i<layer.ol_layer.grid.length; i++) {
                    num_tiles += layer.ol_layer.grid[i].length;
                }
            }
        });
        if (num_tiles > 0) {
            ratio = 1 - num_loading_tiles / num_tiles;
            set_progress(ratio);
        }
        else {
            // no tiled/gridded layers
            ratio = 1 - layers_loading / layers.length;
            set_progress(ratio);
        }
    }

    function set_progress (ratio) {
        // clamp ratio
        if (ratio < 0) ratio = 0;
        if (ratio >= 1) ratio = 1;

        var is_ready = ratio == 1;
        if (is_ready) {
            //$progressbar.addClass('progress-success').removeClass('active').removeClass('progress-striped');
            $progressbar.toggle();
            $btn.removeAttr('disabled');
            $slider.slider('enable');
            if (!$btn.hasClass('active')) {
              start();
            }
            $progressbar.hide();

        }
        else {
            $progressbar.toggle();
            $btn.attr('disabled', 'disabled');
            $slider.slider('disable');
        }
        var pct = ratio * 100 + '%';
        $progressbar.find('.bar').css({width: pct});
    }

    function wait_until_first_layer_loaded () {
        var wait_interval;
        var tick = function () {
            if (layers[0] && layers[0].ol_layer &&
                !layers[0].ol_layer.loading) {
                set_layer(0);
                // stop self
                clearInterval(wait_interval);
            }
        };
        set_progress(0);
        progress_interval = setInterval(update_progress, 300);
        wait_interval = setInterval(tick, 1000);
    }

    function init_overview() {
        var overview_options = {
            size: new OpenLayers.Size(200, 250),
            maximized: true,
            mapOptions: {
                // World Extent
                // restrictedExtent: new OpenLayers.Bounds(
                // -20037508.34, -8400000.00,
                // 20037508.34, 15000000.00
                // ),
                restrictedExtent: new OpenLayers.Bounds(
                    388076.83040199202, 6586328.309563829,
                    760954.7013451669, 7023311.813260503
                ),
                projection: 'EPSG:3857',
                theme: null // KEEP THIS, to prevent OL from dynamically adding
                            // its CSS
            }
        };
        var overview_map = new StaticOverviewMap(overview_options);
        map.addControl(overview_map);

        var mouse_position = new OpenLayers.Control.MousePosition({
            align: 'left',
            displayProjection: 'EPSG:3857'
        });
        map.addControl(mouse_position);
    }

    function addPoweredBy(){
    var powered_by = '<p class="neerslagradar_poweredby">Powered by:  ' +
                     '&nbspRoyal Haskoning DHV&nbsp  |  ' +
                     '&nbspNelen & Schuurmans&nbsp</p>';
    $("#footer").prepend(powered_by);
    }
    function show_map(position) {
        var projWGS84 = new OpenLayers.Projection("EPSG:4326");
        var proj900913 = new OpenLayers.Projection("EPSG:900913");
        var latitude = position.coords.latitude;
        var longitude = position.coords.longitude;
        var lonlat = new OpenLayers.LonLat(longitude, latitude);
        lonlat.transform(projWGS84, proj900913);
        map.setCenter(lonlat);
        map.zoomTo(11);
    }
    function zoomToGeolocation() {
        if (Modernizr.geolocation) {
            navigator.geolocation.getCurrentPosition(show_map);
        }
    }
    function init_neerslagradar () {
        // init_overview();
        var dt_start = moment.utc().subtract('hours', 3);
        var dt_end = moment.utc().add('hours', 3);
        set_view_state({dt_start: dt_start, dt_end: dt_end});
        init_button();
        init_slider();
        init_progress();
        init_geolocation_button();
        init_cycle_layers();
        wait_until_first_layer_loaded();
        addPoweredBy();
    }
    $(document).ready(init_neerslagradar);
})();
