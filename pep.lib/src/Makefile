all: remap

remap: remap.c
	 gcc -O3 -Wall `gdal-config --cflags` remap.c `gdal-config --libs` -lm -o remap
	 mv remap ../bin/
	#gcc -O3  -Wall `gdal-config --cflags` -I/usr/include/hdf/  remap.c `gdal-config --libs` -lm  -lmfhdfalt  -o remap 

clean:
	rm -f *.o remap

install:
