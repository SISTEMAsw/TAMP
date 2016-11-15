(function(){"use strict";var a=this;a.require(["backbone","communicator","globals","hbs!tmpl/wps_getdata","app","papaparse"],function(a,b,c,d,e,f){var g=a.Marionette.Controller.extend({initialize:function(a){this.selection_list=[],this.activeWPSproducts=[],this.activeModels=[],this.selected_time=null,this.listenTo(b.mediator,"map:layer:change",this.changeLayer),this.listenTo(b.mediator,"selection:changed",this.onSelectionChanged),this.listenTo(b.mediator,"time:change",this.onTimeChange),this.listenTo(b.mediator,"analytics:set:filter",this.onAnalyticsFilterChanged)},checkModelValidity:function(){$(".validitywarning").remove();var a=[];if(this.activeModels.length>0)for(var b=this,d=this.activeModels.length-1;d>=0;d--){var e=c.products.find(function(a){return a.get("download").id==b.activeModels[d]});if(e.get("validity")){var f=e.get("validity"),g=new Date(f.start),h=new Date(f.end);this.selected_time&&(this.selected_time.start<g||this.selected_time.end>h)&&a.push({model:e.get("download").id,start:g,end:h})}}if(a.length>0){for(var i="",d=a.length-1;d>=0;d--)i+=a[d].model+":"+g+" - "+h+"<br>";$("#error-messages").append('<div class="alert alert-warning validitywarning"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><strong>Warning!</strong> The current time selection is outside the validity of the model, data is displayed for the last valid date, please take this into consideration when analysing the data.<br>'+i+"Tip: You can see the validity of the model in the time slider.</div>")}},updateLayerResidualParameters:function(){c.products.each(function(a){if("Swarm"==a.get("satellite")){for(var b=a.get("parameters"),c=null,d=_.keys(b),e=d.length-1;e>=0;e--)b[d[e]].residuals&&(b[d[e]].selected&&(c=d[e]),delete b[d[e]]);for(var e=this.activeModels.length-1;e>=0;e--)b[this.activeModels[e]]={range:[-10,40],uom:"nT",colorscale:"jet",name:"Residuals to "+this.activeModels[e],residuals:!0},this.activeModels[e]==c&&(b[this.activeModels[e]].selected=!0),a.set({parameters:b})}},this),b.mediator.trigger("layer:settings:changed")},changeLayer:function(a){if(!a.isBaseLayer){var b=c.products.find(function(b){return b.get("name")==a.name});b&&(a.visible?(b.get("processes")&&_.each(b.get("processes"),function(a){this.activeWPSproducts.push(a.layer_id)},this),b.get("model")&&(this.activeModels.push(b.get("download").id),this.updateLayerResidualParameters())):(_.each(b.get("processes"),function(a){-1!=this.activeWPSproducts.indexOf(a.layer_id)&&this.activeWPSproducts.splice(this.activeWPSproducts.indexOf(a.layer_id),1)},this),-1!=this.activeModels.indexOf(b.get("download").id)&&(this.activeModels.splice(this.activeModels.indexOf(b.get("download").id),1),this.updateLayerResidualParameters()))),this.checkSelections()}this.checkModelValidity()},onSelectionChanged:function(a){a?(this.selection_list.push(a),this.checkSelections()):(this.plotdata=[],this.selection_list=[],this.checkSelections())},onAnalyticsFilterChanged:function(a){c.swarm.set({filters:a})},checkSelections:function(){null==this.selected_time&&(this.selected_time=b.reqres.request("get:time")),this.activeWPSproducts.length>0&&this.selected_time?this.sendRequest():c.swarm.set({data:[]})},onTimeChange:function(a){this.selected_time=a,this.checkSelections(),this.checkModelValidity()},sendRequest:function(){var a=this,b=[];if(c.products.each(function(c){if(-1!=a.activeWPSproducts.indexOf(c.get("views")[0].id)){var d=c.get("processes");_.each(d,function(a){if(a)switch(a.id){case"retrieve_data":b.push({layer:a.layer_id,url:c.get("views")[0].urls[0]})}},this)}},this),b.length>0){var e={collection_ids:b.map(function(a){return a.layer}).join(),begin_time:getISODateTimeString(this.selected_time.start),end_time:getISODateTimeString(this.selected_time.end)};if(this.selection_list.length>0){var g=this.selection_list[0];e.bbox=g.s+","+g.w+","+g.n+","+g.e}var h=_.find(c.products.models,function(a){return null!=a.get("shc")});h&&(e.shc=h.get("shc")),this.activeModels.length>0&&(e.model_ids=this.activeModels.join());var i=d(e);$.post(b[0].url,i).done(function(a){f.parse(a,{header:!0,dynamicTyping:!0,skipEmptyLines:!0,complete:function(a){for(var b=a.data,d=b.length-1;d>=0;d--){if(b[d].hasOwnProperty("Timestamp")&&(b[d].Timestamp=new Date(1e3*b[d].Timestamp)),b[d].hasOwnProperty("B_NEC")){var e=b[d].B_NEC;e=e.slice(1,-1).split(";").map(Number),delete b[d].B_NEC,b[d].B_N=e[0],b[d].B_E=e[1],b[d].B_C=e[2]}if(b[d].hasOwnProperty("B_error")){var e=b[d].B_error;e=e.slice(1,-1).split(";").map(Number),delete b[d].B_error,b[d].B_N_error=e[0],b[d].B_E_error=e[1],b[d].B_C_error=e[2]}$.each(b[d],function(a,c){if(a.indexOf("B_NEC_")>-1){var e=a.substring(6),f=b[d][a];f=f.slice(1,-1).split(";").map(Number),delete b[d][a],b[d]["B_N_res_"+e]=f[0],b[d]["B_E_res_"+e]=f[1],b[d]["B_C_res_"+e]=f[2]}})}c.swarm.set({data:a.data})}})})}}});return new g})}).call(this);