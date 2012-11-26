// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, map */

function MyLayer (dt) {
    this.dt = dt;
    this.ol_layer = null;
}

var CssHideableWMS = OpenLayers.Class(OpenLayers.Layer.WMS, {
    cssVisibility: true,

    initialize: function (name, url, params, options) {
        OpenLayers.Layer.WMS.prototype.initialize.apply(this, [name, url, params, options]);
        if (options.cssVisibility === true || options.cssVisibility === false) {
            this.cssVisibility = options.cssVisibility;
        }
        this.events.on({'added': this.updateCssVisibility, 'moveend': this.updateCssVisibility, scope: this});
    },

    destroy: function () {
        this.events.un({'added': this.updateCssVisibility, 'moveend': this.updateCssVisibility, scope: this});
        OpenLayers.Layer.WMS.prototype.destroy.apply(this);
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

var CssHideableImageLayer = OpenLayers.Class(OpenLayers.Layer.Image, {
    cssVisibility: true,

    initialize: function (name, url, extent, size, options) {
        OpenLayers.Layer.Image.prototype.initialize.apply(this, [name, url, extent, size, options]);
        if (options.cssVisibility === true || options.cssVisibility === false) {
            this.cssVisibility = options.cssVisibility;
        }
        this.events.on({'added': this.updateCssVisibility, 'moveend': this.updateCssVisibility, scope: this});
    },

    destroy: function () {
        this.events.un({'added': this.updateCssVisibility, 'moveend': this.updateCssVisibility, scope: this});
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
        OpenLayers.Control.OverviewMap.prototype.initialize.apply(this, [options]);
        if (options.staticMap === true || options.staticMap === false) {
            this.staticMap = options.staticMap;
        }
    },

    updateOverview: function() {
        var mapRes = this.map.getResolution();
        var targetRes = this.ovmap.getResolution();
        var resRatio = targetRes / mapRes;
        if(resRatio > this.maxRatio) {
            // zoom in overview map
            targetRes = this.minRatio * mapRes;            
        } else if(resRatio <= this.minRatio) {
            // zoom out overview map
            targetRes = this.maxRatio * mapRes;
        }
        if (!this.staticMap) {
            var center;
            if (this.ovmap.getProjection() != this.map.getProjection()) {
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

var start_dt = moment.utc(fixed_start_dt);
var layers = [];

for (var i=0; i<288; i+=3) {
    layers.push(new MyLayer(moment.utc(start_dt).add('minutes', 5 * i)));
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
        }
        if (layer_idx != -1) {
            var layer = layers[layer_idx];
            layer.ol_layer.setCssVisibility(true);
        }

        // update with next layer index
        current_layer_idx = layer_idx;

        on_layer_changed();
    }
}

function cycle_layers () {
    var current_layer = layers[current_layer_idx];

    // don't swap layers when we're still loading
    if (!current_layer.ol_layer.loading) {
        // figure out next layer
        var next_layer_idx = (current_layer_idx >= layers.length - 1) ? 0 : current_layer_idx + 1;
        set_layer(next_layer_idx);
    }
}

function init_cycle_layers () {
/*
    $.each(layers, function (idx, layer) {
        var dt_iso_8601 = layer.dt.format('YYYY-MM-DDTHH:mm:ss') + '.000Z';
        var ol_layer = new CssHideableWMS(
            'L' + idx,
            wms_base_url,
            {
                layers: layer.wms_name,
                time: dt_iso_8601
            },
            {
                buffer: 0,
                singleTile: true,
                tileLoadingDelay: 2000,
                isBaseLayer: false,
                visibility: true, // keep this, so all layers are preloaded in the browser
                cssVisibility: false, // hide layer with this custom option
                displayInLayerSwitcher: false,
                metadata: layer,
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
    });
*/

    var bbox = new OpenLayers.Bounds(fixed_image_layer_bbox.split(','));
    $.each(layers, function (idx, layer) {
        var dt_iso_8601 = layer.dt.format('YYYY-MM-DDTHH:mm:ss') + '.000Z';
        var wms_params = {
            WIDTH: 512,
            HEIGHT: 512,
            SRS: 'EPSG:3857',
            BBOX: bbox.toBBOX(),
            TIME: dt_iso_8601
        };
        var wms_url = wms_base_url + '?' + $.param(wms_params);
        var ol_layer = new CssHideableImageLayer(
            'L' + idx,
            wms_url,
            bbox,
            new OpenLayers.Size(512, 512),
            {
                isBaseLayer: false,
                alwaysInRange: true,
                visibility: true, // keep this, so all layers are preloaded in the browser
                cssVisibility: false, // hide layer again with this custom option
                displayInLayerSwitcher: false,
                metadata: layer,
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
    });
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
            $("#currentdt").html(layer.dt.format('LLL'));
        },
        slide: function (event, ui) {
            stop_if_running();
            set_layer(ui.value);
            // hack: force triggering a change event while sliding
            var slider_data = $slider.data('slider');
            slider_data._trigger('change', event, ui)
        }
    });
}

function start () {
    $btn.find('i').removeClass('icon-play').addClass('icon-pause');
    $btn.addClass('active');
    $btn.find('span').html('Stop animatie');
    cycle_layers_interval = setInterval(cycle_layers, interval_ms);
}

function stop () {
    $btn.find('i').removeClass('icon-pause').addClass('icon-play');
    $btn.removeClass('active');
    $btn.find('span').html('Start animatie');
    clearInterval(cycle_layers_interval);
    cycle_layers_interval = null;
}

function stop_if_running () {
    if (is_running()) {
        stop();
    }
}

function is_running () {
    return cycle_layers_interval != null;
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

function init_progress () {
    $progressbar = $('#progressbar');
}

function on_layer_loading_change () {
    if (layers_loading > 0) {
        // 'if' control structure split for clarity
        if (progress_interval == null) {
            set_progress(0);
            progress_interval = setInterval(update_progress, 300);
        }
    }
    else {
        if (progress_interval != null) {
            clearInterval(progress_interval);
            progress_interval = null;
            set_progress(1);
        }
    }
}

function update_progress () {
    var num_loading_tiles = 0;
    var num_tiles = 0;
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
        var ratio = 1 - num_loading_tiles / num_tiles;
        set_progress(ratio);
    }
    else {
        // no tiled/gridded layers
        var ratio = 1 - layers_loading / layers.length;
        set_progress(ratio);
    }
}

function set_progress (ratio) {
    // clamp ratio
    if (ratio < 0) ratio = 0;
    if (ratio >= 1) ratio = 1;

    var is_ready = ratio == 1;
    if (is_ready) {
        $progressbar.addClass('progress-success').removeClass('active');
        $btn.removeAttr('disabled'); 
        $slider.slider('enable');
    }
    else {
        $progressbar.removeClass('progress-success').addClass('active');
        $btn.attr('disabled', 'disabled');
        $slider.slider('disable');
    }
    var pct = ratio * 100 + '%';
    $progressbar.find('.bar').css({width: pct});
}

function wait_until_first_layer_loaded () {
    var wait_interval;
    var tick = function () {
        if (layers[0] && layers[0].ol_layer && !layers[0].ol_layer.loading) {
            set_layer(0);
            // stop self
            clearInterval(wait_interval);
        }
    };
    wait_interval = setInterval(tick, 1000);
}

function init_background_layer() {
    map.removeLayer(map.baseLayer);
    var layer = new OpenLayers.Layer.Stamen('toner-lite');
    map.addLayer(layer);
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
            theme: null // KEEP THIS, to prevent OL from dynamically adding its CSS
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

function init_neerslagradar () {
    init_background_layer();
    init_overview();
    init_button();
    init_slider();
    init_progress();
    init_cycle_layers();
    wait_until_first_layer_loaded();
}

$(document).ready(init_neerslagradar);
