define(["core/BaseView","app","communicator","globals","./VirtualGlobeViewer/app"],function(a,b,c,d,e){"use strict";var f=a.extend({tagName:"canvas",className:"globe",initialize:function(b){a.prototype.initialize.call(this,b),this.enableEmptyView(!1),this.selectinType=null,this._startPosition=b.startPosition,"undefined"==typeof this._startPosition&&(this._startPosition={geoCenter:[15,47],distance:0,duration:3e3,tilt:40}),this.currentToI=this.toi()},didInsertElement:function(){this.getViewer()||(this.setViewer(this._createVGV()),this.getViewer().setToI(this.toi()),this._setLayersFromAppContext(),this.zoomTo(this._startPosition)),this.listenTo(c.mediator,"selection:changed",this._addAreaOfInterest),this.listenTo(c.mediator,"selection:activated",this._onSelectionActivated),this.listenTo(c.mediator,"map:setUrl",this.zoomTo),this.listenTo(c.mediator,"map:center",this._onMapCenter),this.listenTo(c.mediator,"map:layer:change",this._onLayerChange),this.listenTo(c.mediator,"time:change",this._onTimeChange),this.listenTo(c.mediator,"productCollection:updateOpacity",this._onOpacityChange),this.listenTo(c.mediator,"productCollection:sortUpdated",this._sortOverlayLayers),this.listenTo(c.mediator,"options:colorramp:change",this._colorRampChange)},didRemoveElement:function(){},supportsLayer:function(a){var b=_.find(a.get("views"),function(a){return"w3ds"===a.protocol.toLowerCase()&&"vertical_curtain"===a.type.toLowerCase()||"wms"===a.protocol.toLowerCase()||"wmts"===a.protocol.toLowerCase()});return b?b:null},onStartup:function(a){this.getViewer().clearCache(),_.forEach(a,function(a,b){this.getViewer().addLayer(a.model,a.isBaseLayer)}.bind(this)),this._sortOverlayLayers()},onResize:function(){this.getViewer()&&this.getViewer().updateViewport()},onLayerAdd:function(a,b){this.getViewer().addLayer(a,b)},onLayerRemove:function(a,b){this.getViewer().removeLayer(a,b)},_addAreaOfInterest:function(a,b,c){if("single"==this.selectionType&&this.getViewer().removeFeatures(),b){var d=this._hexToRGB(c);this.getViewer().addAreaOfInterest(b,[d.r/255,d.g/255,d.b/255,1])}},_hexToRGB:function(a){var b=/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(a);return b?{r:parseInt(b[1],16),g:parseInt(b[2],16),b:parseInt(b[3],16)}:null},_removeAllOverlays:function(){this.getViewer().removeAllOverlays()},_onOpacityChange:function(a){this.getViewer().onOpacityChange(a.model.get("name"),a.value)},_onTimeChange:function(a){this.currentToI=a;var b=new Date(a.start),c=new Date(a.end);this.getViewer().setToI(b.toISOString()+"/"+c.toISOString())},_onSelectionActivated:function(a){this.selectionType=a.selectionType,a.active?this.getViewer().enableAOISelection(a.id,this.selectionType):this.getViewer().disableAOISelection()},toi:function(){var a=this.currentToI;if(!a){var b=new Date(this.legacyContext().timeOfInterest.start),c=new Date(this.legacyContext().timeOfInterest.end);a=this.currentToI=b.toISOString()+"/"+c.toISOString()}return a},_sortOverlayLayers:function(){this.getViewer().sortOverlayLayers()},_onMapCenter:function(a){var b=0;switch(a.l){case 0:b=5e7;break;case 1:b=3e7;break;case 2:b=18e6;break;case 3:b=9e6;break;case 4:b=48e5;break;case 5:b=24e5;break;case 6:b=12e5;break;case 7:b=7e5;break;case 8:b=3e5;break;case 9:b=8e4;break;case 10:b=3e4;break;case 11:b=9e3;break;case 12:b=7e3;break;case 13:b=5e3;break;case 14:b=4e3}var c={center:[a.x,a.y],distance:b,duration:100};this.zoomTo(c)},zoomTo:function(a){this.getViewer().zoomTo(a)},setTilt:function(a,b){this.getViewer().setTilt(a,b)},_createVGV:function(){function a(a){var b=13;return a>0&&.0024>=a?b=13:a>.0024&&.004>=a?b=12:a>.004&&.0047>=a?b=11:a>.0047&&.017>=a?b=10:a>.017&&.03>=a?b=9:a>.03&&.07>=a?b=8:a>.07&&.18>=a?b=7:a>.18&&.5>=a?b=6:a>.5&&.2>=a?b=5:a>.2&&1>=a?b=4:a>1&&2>=a?b=3:a>2&&2.8>=a?b=2:a>2.8&&(b=1),b}var b=new e({canvas:this.el,w3dsBaseUrl:c.mediator.config.backendConfig.W3DSDataUrl});return b.setOnPanEventCallback(function(b,d,e){var f=b.save(),g=f.distance;this.stopListening(c.mediator,"map:center"),c.mediator.trigger("map:center",{x:f.geoCenter[0],y:f.geoCenter[1],l:a(g)}),this.listenTo(c.mediator,"map:center",this._onMapCenter)}.bind(this)),b.setOnZoomEventCallback(function(b,d,e){var f=b.save(),g=f.distance;this.stopListening(c.mediator,"map:center"),c.mediator.trigger("map:center",{x:f.geoCenter[0],y:f.geoCenter[1],l:a(g)}),this.listenTo(c.mediator,"map:center",this._onMapCenter)}.bind(this)),b.setOnNewAOICallback(function(a){for(var b=[],d=0;d<a.length;d++)b.push(new OpenLayers.Geometry.Point(a[d].x,a[d].y));var e=new OpenLayers.Geometry.LinearRing(b),f=new OpenLayers.Geometry.Polygon([e]),g=new OpenLayers.Feature.Vector(f);this.stopListening(c.mediator,"selection:changed"),c.mediator.trigger("selection:changed",g,a),this.listenTo(c.mediator,"selection:changed",this._addAreaOfInterest)}.bind(this)),b.setColorRamp(c.mediator.colorRamp),b},_colorRampChange:function(a){this.getViewer().setColorRamp(a)},_dumpLayerConfig:function(){this.getViewer().dumpLayerConfig()}});return f});