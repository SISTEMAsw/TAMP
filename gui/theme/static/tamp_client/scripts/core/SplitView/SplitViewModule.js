define(["backbone.marionette","app","communicator","./SplitViewController"],function(a,b,c,d){"use strict";b.module("SplitView",function(a){this.startsWithParent=!0,this.on("start",function(a){this.instances={},this.idx=0,console.log("[SplitView] Finished module initialization")}),this.createController=function(a){var b=void 0;"undefined"!=typeof a&&(b=a.id),"undefined"==typeof b&&(b="SplitView."+this.idx++);var c=new d;return this.instances[b]=c,c}})});