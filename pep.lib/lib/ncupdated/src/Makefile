all: gtiff2nc nctimextract updatenc

nctimextract: nctimextract.c
	gcc -Wall -I/usr/local/include/ `gdal-config --cflags` nctimextract.c -lnetcdf `gdal-config --libs` -o nctimextract


gtiff2nc: gtiff2nc.c
	gcc -Wall -I/usr/local/include/ `gdal-config --cflags` gtiff2nc.c -lnetcdf `gdal-config --libs` -o gtiff2nc

updatenc: updatenc.c
	gcc -Wall -I/usr/local/include/ `gdal-config --cflags` updatenc.c -lnetcdf `gdal-config --libs` -o updatenc


clean:
	rm -f gtiff2nc nctimextract updatenc
