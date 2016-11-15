(function(){"use strict";var a=this;a.require(["backbone","communicator","globals","app","views/DownloadView","views/DownloadFilterView","models/DownloadModel"],function(a,b,c,d,e,f,g){var h=a.Marionette.Controller.extend({model:new g.DownloadModel,initialize:function(a){this.model.set("products",{}),this.listenTo(b.mediator,"map:layer:change",this.onChangeLayer),this.listenTo(b.mediator,"time:change",this.onTimeChange),this.listenTo(b.mediator,"selection:changed",this.onSelectionChange),this.listenTo(b.mediator,"dialog:open:download",this.onDownloadToolOpen),this.listenTo(b.mediator,"analytics:set:filter",this.onDownloadSetFilter),this.listenTo(b.mediator,"dialog:open:download:filter",this.onDownloadToolFilterOpen)},onChangeLayer:function(a){if(!a.isBaseLayer){var b=c.products.find(function(b){return b.get("name")==a.name});if(b){var d=this.model.get("products");a.visible?d[b.get("download").id]=b:delete d[b.get("download").id],this.model.set("products",d)}}this.checkDownload()},onTimeChange:function(a){this.model.set("ToI",a),this.checkDownload()},onDownloadSetFilter:function(a){this.model.set("filter",a)},onSelectionChange:function(a){null!=a?this.model.set("AoI",a):this.model.set("AoI",null),this.checkDownload()},checkDownload:function(){null!=this.model.get("ToI")&&null!=this.model.get("AoI")&&_.size(this.model.get("products"))>0?b.mediator.trigger("selection:enabled",{id:"download",enabled:!0}):b.mediator.trigger("selection:enabled",{id:"download",enabled:!1})},onDownloadToolOpen:function(a){a?d.viewContent.show(new e.DownloadView({model:this.model})):d.viewContent.close()},onDownloadToolFilterOpen:function(a){a?d.viewContent.show(new f.DownloadFilterView({model:this.model})):d.viewContent.close()}});return new h})}).call(this);