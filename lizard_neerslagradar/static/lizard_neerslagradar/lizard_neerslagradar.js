// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, map, lizard_neerslagradar */

(function () {
    function MyLayer (dt, opacity, bbox) {
        this.dt = dt;
        this.opacity = opacity;
        this.bbox = bbox;
        this.ol_layer = null;
    }

    var CssHideableWMS = OpenLayers.Class(OpenLayers.Layer.WMS, {
        cssVisibility: true,

        initialize: function (name, url, params, options) {
            OpenLayers.Layer.WMS.prototype.initialize.apply(
                this, [name, url, params, options]);
            if (options.cssVisibility === true || options.cssVisibility === false) {
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
            OpenLayers.Layer.Image.prototype.initialize.apply(
                this, [name, url, extent, size, options]);
            if (options.cssVisibility === true || options.cssVisibility === false) {
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
            OpenLayers.Control.OverviewMap.prototype.initialize.apply(this, [options]);
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
    var paused_at_end = false;
    var is_first_load = true;

    var layers = [];
    var regional_layers = [];

    var full_bbox = new OpenLayers.Bounds(
        lizard_neerslagradar.fixed_image_layer_bbox.split(','));

    var regional_bbox;
    if (lizard_neerslagradar.user_logged_in) {
        regional_bbox = new OpenLayers.Bounds(
            lizard_neerslagradar.region_bbox.split(','));
    }

    for (var i=0; i < lizard_neerslagradar.animation_datetimes.length; i++) {
        var dt = moment.utc(lizard_neerslagradar.animation_datetimes[i].datetime);

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
            (!lizard_neerslagradar.user_logged_in ||
             !regional_layer ||
             !regional_layer.ol_layer.loading)) {
            // figure out next layer
            var next_layer_idx = (current_layer_idx >= layers.length - 1) ? 0 : current_layer_idx + 1;
            if (next_layer_idx === 0) {
                paused_at_end = true;
                setTimeout(function () { paused_at_end = false; set_layer(0); }, 1000);
            }
            else {
                set_layer(next_layer_idx);
            }
        }
    }

    function init_cycle_layers () {
        var init_layer = function (idx, layer) {
            var dt_iso_8601 = layer.dt.format('YYYY-MM-DDTHH:mm:ss') + '.000Z';
            var wms_params = {
                WIDTH: 525,
                HEIGHT: 497,
                SRS: 'EPSG:3857',
                BBOX: layer.bbox.toBBOX(),
                TIME: dt_iso_8601
            };
            var wms_url = lizard_neerslagradar.wms_base_url + '?' + $.param(wms_params);
            var ol_layer = new CssHideableImageLayer(
                'L' + idx,
                wms_url,
                layer.bbox,
                new OpenLayers.Size(525, 497),
                {
                    isBaseLayer: false,
                    alwaysInRange: true,
                    visibility: true, // keep this, so all layers are preloaded in the browser
                    cssVisibility: false, // hide layer again with this custom option
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

    function start_if_first_load () {
        if (is_first_load) {
            start();
            is_first_load = false;
        }
    }

    function start () {
        $btn.find('i').removeClass('icon-play').addClass('icon-pause');
        $btn.addClass('active');
        cycle_layers_interval = setInterval(cycle_layers, interval_ms);
    }

    function stop () {
        $btn.find('i').removeClass('icon-pause').addClass('icon-play');
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

    function init_progress () {
        $progressbar = $('#progressbar');
    }

    function on_layer_loading_change () {
        if (layers_loading > 0) {
            // 'if' control structure split for clarity
            if (progress_interval === null) {
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
            $progressbar.addClass('progress-success').removeClass('active');
            $progressbar.hide();
            $btn.removeAttr('disabled');
            $slider.slider('enable');
            start_if_first_load();
        }
        else {
            $progressbar.removeClass('progress-success').addClass('active');
            $progressbar.show();
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
        // init_overview();
        init_button();
        init_slider();
        init_progress();
        init_cycle_layers();
        wait_until_first_layer_loaded();
    }

    $(document).ready(init_neerslagradar);
})();
