define(["backbone","app","communicator","./RectangularBoxView"],function(a,b,c,d){"use strict";var e=a.Marionette.Controller.extend({initialize:function(a){this.createView()},createView:function(){this.view=new d({context:c.mediator,x3dtag_id:"x3d",x3dscene_id:"x3dScene",x3dhidden_id:"x3dom-hidden"})},getView:function(){return this.view},isActive:function(){return!this.view.isClosed}});return e});