define(["jquery"],function(a){"use strict";function b(a){dat.GUI.prototype.removeFolder=function(a){this.__folders[a]&&(this.__folders[a].close(),this.__folders[a]=void 0,this.onResize())},this.mainGUI=null,this.idx=0,this.renderer=null,this.cameraPosition=a.cameraPosition||[120,80,160],this.backgroundColor=a.backgroundColor||[1,1,1],this.container=a.elem,this.animSpeed=1;var b=this.renderer=new X.renderer3D;b.container=a.elem,b.bgColor=this.backgroundColor,b.init(),this.volumes={},this.meshes={},this.volumes_to_add=[],this.meshes_to_add=[],b.camera.position=this.cameraPosition}function c(a){for(var b=new ArrayBuffer(a.length),c=new Uint8Array(b),d=0,e=a.length;e>d;d++)c[d]=a.charCodeAt(d);return b}return b.prototype.createRenderer=function(){var a=this.renderer=new X.renderer3D;a.container=this.container,a.bgColor=this.backgroundColor,a.init(),a.camera.position=this.cameraPosition},b.prototype.onResize=function(){this.renderer._width=this.renderer._container.clientWidth,this.renderer._height=this.renderer._container.clientHeight,this.renderer._canvas.width=this.renderer._container.clientWidth,this.renderer._canvas.height=this.renderer._container.clientHeight,this.renderer.resetBoundingBox(),this.renderer.resetViewAndRender()},b.prototype.addMesh=function(a){("undefined"==typeof this.renderer||null==this.renderer)&&this.createRenderer();var b=Object.keys(a.models[0]),c=a.models[0][b[0]],d=a.mtls[0][b[0].split(".")[0]+".mtl"];console.log("[XTKViewer.addMesh] adding obj/mtl pair: "+b[0]);var e=K3D.parse.fromOBJ(c);console.log("OBJ (K3D) stats:"),console.log(" * objects: "+Object.keys(e.groups).length),_.forEach(Object.keys(e.groups),function(a,b){var c=e.groups[a];console.log(" * name:     "+a),console.log(" * verts:     "+(c.to-c.from)),console.log(" * faces:     "+(c.to-c.from)/3)});for(var f=K3D.parse.toIndividualOBJs(e),g=K3D.parse.fromMTL(d),h=new X.object,i=0;i<f.length;i++){var e=f[i].data,j=f[i].name,k=f[i].material,l=new X.mesh;if(l.file=j+".obj",l.filedata=K3D.parse._strToBuff(e),k&&g[k]){var m=g[k].map_Kd;l.texture._image=new Image,l.texture.flipY=!0;var n=_.find(a.textures,function(a){return a[m]?!0:!1}),o=Object.keys(n)[0];l.texture._image.src=K3D.convertToPNGURI(n[o])}l.color=[0,1,0],h.children.push(l)}var p=a.label||"Curtain",q=this.meshes[a.label];q?(q=this.meshes[a.label],p+=" "+(q.length+1)):(this.meshes[a.label]=[],q=this.meshes[a.label],p+=" "+(q.length+1));var r={label:p,object:h,gui:null};q.push(r),this.meshes_to_add.push(r),this.renderer._onShowtime=!1,this.renderer.onShowtime=function(){if(!this.mainGUI){var a=this.mainGUI=new dat.GUI({autoPlace:!0});this.renderer.container.appendChild(a.domElement)}for(var b=0;b<this.meshes_to_add.length;b++){var c=this.meshes_to_add[b],a=this.addMeshToGUI(c.label,c.object);c.gui=a;var d=[0,0,0];_.forEach(c.object.children,function(a){a.transform.scale(200,200,200);var b=a.points._centroid,c=(d[0]+b[0])/2,e=(d[1]+b[1])/2,f=(d[2]+b[2])/2;d=[c,e,f]}),this.renderer.camera.position=[0,0,-3],this.renderer.camera.focus=d}this.meshes_to_add=[]}.bind(this),this.renderer.add(h),this.renderer.render()},b.prototype.addVolume=function(a){("undefined"==typeof this.renderer||null==this.renderer)&&this.createRenderer();var b=null;if(b=a.data["application/x-nifti"]?a.data["application/x-nifti"]:a.data["application/octet-stream"],!b)return void console.log("[XTKViewer::addVolume] AoI contains no volume data, skipping...");for(var d=Object.keys(b).length,e=0;d>e;e++){var f=b[e],g=Object.keys(f),h=new X.volume;h.file=a.filename+"&dummy.nii";var i=f[g[0]];"string"==typeof i?h.filedata=c(f[g[0]]):h.filedata=f[g[0]],h.volumeRendering=a.volumeRendering||void 0,h.opacity=a.opacity||void 0,h.minColor=a.minColor||void 0,h.maxColor=a.maxColor||void 0,h.reslicing=a.reslicing||void 0;var j=a.label||"Volume",k=this.volumes[a.filename];k?(k=this.volumes[a.filename],j+=" "+(k.length+1)):(this.volumes[a.filename]=[],k=this.volumes[a.filename],j+=" "+(k.length+1));var g={label:j,object:h,gui:null};k.push(g),this.volumes_to_add.push(g),this.renderer.add(h)}this.renderer._onShowtime=!1,this.renderer.onShowtime=function(a){if(!this.mainGUI){var b=this.mainGUI=new dat.GUI({autoPlace:!0});this.renderer.container.appendChild(b.domElement),this.baseInitDone=!0}for(var c=0;c<this.volumes_to_add.length;c++){var d=this.volumes_to_add[c],b=this.addVolumeToGUI(d.label,d.object);d.gui=b}this.volumes_to_add=[]}.bind(this,k),this.renderer.render()},b.prototype.removeObject=function(a){var b=this.volumes[a]||this.meshes[a];b&&(_.forEach(b,function(a){a&&a.object&&a.object._children?(this.renderer.remove(a.object),a.gui&&this.removeGui(a.gui)):console.log("[XTKViewer::removeObject] Trying to remove invalid object, this should not happen!")}.bind(this)),this.volumes[a]?delete this.volumes[a]:delete this.meshes[a],0===Object.keys(this.volumes).length&&0===Object.keys(this.meshes).length&&(this.onResize(),this.mainGUI&&(this.removeGui(this.mainGUI),this.mainGUI=null)))},b.prototype.addVolumeToGUI=function(a,b){var c=this.mainGUI.addFolder(a),d=(c.add(b,"volumeRendering").name("Volume Rendering"),c.addFolder("Segmentation Settings"));d.addColor(b,"minColor"),d.addColor(b,"maxColor"),d.add(b,"opacity",0,1).listen(),d.add(b,"lowerThreshold",b.min,b.max+1e-4),d.add(b,"upperThreshold",b.min,b.max+1e-4),d.add(b,"windowLow",b.min,b.max),d.add(b,"windowHigh",b.min,b.max);var e=c.addFolder("Slicing");e.add(b,"indexX",0,b.range[0]-1),e.add(b,"indexY",0,b.range[1]-1),e.add(b,"indexZ",0,Math.round(b.range[2]-1));var f=function(a,b,c){if(this.volume=a,this.speed=c||1,this.isStarted=!1,this.curIdx=0,this.speed=c,this.oldSpeed=c,this.axisMembers=["indexX","indexY","indexZ"],"x"===b)this.axis=this.axisMembers[0],this.maxIdx=a.range[0]+1;else if("y"===b)this.axis=this.axisMembers[1],this.maxIdx=a.range[1]+1;else{if("z"!==b)throw Error("[AnimateAxis::ctor] no valid axis given!");this.axis=this.axisMembers[2],this.maxIdx=a.range[2]+1}this.stop=function(){clearInterval(this.handle),this.isStarted=!1},this.start=function(){this.isStarted?this.stop():(this.handle=setInterval(function(){this.curIdx>this.maxIdx&&(this.curIdx=0),this.volume[this.axis]=this.curIdx++,this.speed!==this.oldSpeed&&(this.stop(),this.start())}.bind(this),this.speed),this.isStarted=!0)}},g=200,h=c.addFolder("Animation Settings"),i=new f(b,"x",g);h.add(i,"start").name("Toggle x-axis animation"),h.add(i,"speed",0,g).name("X animation speed").step(1);var j=new f(b,"y",g);h.add(j,"start").name("Toggle y-axis animation"),h.add(j,"speed",0,g).name("Y animation speed").step(1);var k=new f(b,"z",g);return h.add(k,"start").name("Toggle z-axis animation"),h.add(k,"speed",0,g).name("Z animation speed").step(1),c.open(),c},b.prototype.addMeshToGUI=function(a,b){var c=this.mainGUI.addFolder(a+this.idx++);c.add(b,"visible");return c.open(),c},b.prototype.reset=function(){_.each(_.keys(this.volumes),function(a){this.removeObject(a)},this),_.each(_.keys(this.meshes),function(a){this.removeObject(a)},this),this.mainGUI&&this.removeGui(this.mainGUI)},b.prototype.destroy=function(){_.each(_.keys(this.volumes),function(a){this.removeObject(a)},this),_.each(_.keys(this.meshes),function(a){this.removeObject(a)},this),this.renderer.destroy(),this.mainGUI&&this.removeGui(this.mainGUI)},b.prototype.removeGui=function(a){var b=a.domElement;b.parentNode.removeChild(b)},b});