#include <stdio.h>
#include <stdlib.h>
#include <netcdf.h>
#include <string.h>
#include <gdal.h>

// updatenc $(pwd)/20150623_006_00_006.nc '/vsicurl/http://mwcs:80/wcs?service=WCS&Request=GetCoverage&coverageid=MOD11_L2_LST@4326_001&subset=t(1435060200)&subset=Long(-12,31)&subset=Lat(32,70)&format=image/tiff'  2t 0 0

int main(int argc, char **argv){
	int i, j, k;
	char	*nc_name	= NULL;
	char	*tiff_name	= NULL;
	char	*SUBDATASET	= NULL;

	int	status		= -1;
	int	ncid		= -1;
	int	varid		= -1;
	int	nd		= 0;
	int	*paDimIds 	= NULL;
	size_t	xdim		= -1;
	size_t	ydim		= -1;
	size_t	ldim		= -1;
	size_t	tdim		= -1;

	float	*data_in	= NULL;
	int	*data_hit	= NULL;
	int	time     	= 0;
	int	altitude 	= 0;
	double	GeoTransform[6] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
	char	*tmp		= NULL;

	GDALDatasetH	hSrcDS;
	GDALRasterBandH	hBandSrc;
	int		pxSizeX 		= 0;
	int		pxSizeY 		= 0;
	int		types			= 0;
	float		*data_tiff 		= NULL;
	double 		padfGeoTransform[6] 	= {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
	double 		invfGeoTransform[6] 	= {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
	double 		x, y, lon, lat;

	GDALAllRegister();

	// ---------------------------------------------------- // 


	if (argc < 5){
		printf("updatenc IN_NETCDF IN_GEOTIFF LAYER N_TIME_LAYER N_ALT_LAYER\n");
		return 0;

	}

	nc_name		= argv[1];
	tiff_name 	= argv[2];
	SUBDATASET	= (char *)malloc( ( strlen(argv[3]) + 1 ) * sizeof(char) ); bzero(SUBDATASET, strlen(argv[3]) ); strcpy(SUBDATASET, argv[3]);
	time		= atoi(argv[4]);
	altitude	= atoi(argv[5]);
	tmp		= (char *)malloc( ( strlen(nc_name) + 10 ) * sizeof(char) ); bzero(tmp, strlen(nc_name) + 10);

	sprintf(tmp, "NETCDF:\"%s\":%s", nc_name, SUBDATASET);


	if ( (hSrcDS = GDALOpen( tmp, GA_ReadOnly )) == NULL ){
		printf("Unable open src file %s\n", tmp);
		printf("Try to open netCDF single layer ...\n");
		if ( (hSrcDS = GDALOpen( nc_name, GA_ReadOnly )) == NULL ){
			printf("Unable open src file %s\n", nc_name);
			return 1;
		}
		time = altitude = 0;
	}

        if ( GDALGetGeoTransform( hSrcDS, GeoTransform ) == CE_Failure ){
                printf("Image no transform can be fetched...\n");
		return 0;
        }
        if ( GDALGetGeoTransform( hSrcDS, padfGeoTransform ) == CE_Failure ){
                printf("Image no transform can be fetched...\n");
		return 0;
        }

	GDALClose(hSrcDS);	


	status = nc_open(nc_name, NC_WRITE, &ncid);
	if(status != NC_NOERR) { printf("nc_open\n");		return 1; }

	status = nc_inq_varid(ncid, SUBDATASET, &varid);
	if(status != NC_NOERR) {
		int nvars;
		nc_inq_nvars(ncid, &nvars);
		for ( varid = 0; varid < nvars; varid++){
			nc_inq_var(ncid, varid, tmp, NULL, NULL, NULL, NULL);
			if ( ! strcmp(tmp, "lon" ) ) continue;
			if ( ! strcmp(tmp, "lat" ) ) continue;
			if ( ! strcmp(tmp, "time") ) continue;
	
			break;
		}
		if (varid == nvars ) { printf("nc_inq_varid\n"); return 1; }

		printf("Found varid: %d with name: %s\n", varid, tmp);

	}

	nc_inq_varndims ( ncid, varid, &nd );
	nc_inq_vardimid(  ncid, varid, paDimIds ); paDimIds = (int *)malloc(nd * sizeof(int));
	nc_inq_vardimid(  ncid, varid, paDimIds );



	nc_inq_dimlen ( ncid, paDimIds[nd-1], &xdim );
	nc_inq_dimlen ( ncid, paDimIds[nd-2], &ydim );
	nc_inq_dimlen ( ncid, paDimIds[nd-3], &ldim );
	nc_inq_dimlen ( ncid, paDimIds[nd-4], &tdim );


	xdim = ( (int)xdim <= 0 ) ? 1 : xdim;
	ydim = ( (int)ydim <= 0 ) ? 1 : ydim;
	ldim = ( (int)ldim <= 0 ) ? 1 : ldim;
	tdim = ( (int)tdim <= 0 ) ? 1 : tdim;



	data_in  = (float *)malloc(sizeof(float) * (int)xdim * (int)ydim * (int)ldim * (int)tdim );
	if(data_in == NULL)    { printf("malloc\n"); 		return 1; }

	data_hit = (int *)malloc(sizeof(int) * (int)xdim * (int)ydim );
	if(data_hit == NULL)    { printf("malloc\n"); 		return 1; }



	printf("Loading NetCDF layer %s (%dx%dx%dx%d)...\n", SUBDATASET, xdim, ydim, ldim, tdim);
	status = nc_get_var_float(ncid, varid, data_in);
	if(status != NC_NOERR) { printf("nc_get_var_float\n"); 	return 1; }

	for(i = 0; i < 6; i++) printf("GeoTransform[%d]: %f\n", i, GeoTransform[i]);


	// ---------------------------------------------------- // 
	printf("Loading new layer %s ...\n", tiff_name );
	if ( (hSrcDS = GDALOpen( tiff_name, GA_ReadOnly )) == NULL ){
		printf("Unable open src file %s\n", tiff_name);
		return 1;
	}

        if ( GDALGetGeoTransform( hSrcDS, padfGeoTransform ) == CE_Failure ){
                printf("Image no transform can be fetched...\n");
		return 1;
        }


	for(i = 0; i < 6; i++) printf("padfGeoTransform[%d]: %f\n", i, padfGeoTransform[i]);

	pxSizeX  = GDALGetRasterXSize(hSrcDS);
	pxSizeY  = GDALGetRasterYSize(hSrcDS);
	hBandSrc = GDALGetRasterBand( hSrcDS, 1 );
	types	 = GDALGetRasterDataType(hBandSrc);

	data_tiff = (float *)malloc( sizeof(float)*  pxSizeX * pxSizeY);
	if(data_tiff == NULL)    { printf("malloc\n");	return 1; }


	if ( types == GDT_Float32 ){
		GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_tiff, pxSizeX, pxSizeY, types, 0, 0);

	} else if ( types == GDT_UInt16 ){
		unsigned short int 	*data_tiff_UInt16 	= NULL;
	        double 			nodata 			= 0.0;
	        double 			scale  			= 1.0;
	        double 			offset 			= 0.0;
		int     		pbSuccess               = 0;

		data_tiff_UInt16 = (unsigned short int *)malloc( sizeof(unsigned short int) *  pxSizeX * pxSizeY);
		if( data_tiff_UInt16 == NULL)    { printf("malloc\n");  return 1; }

		nodata   = GDALGetRasterNoDataValue(    hBandSrc, &pbSuccess); if( ! pbSuccess ) nodata = 0;   
                scale    = GDALGetRasterScale(          hBandSrc, &pbSuccess); if( ! pbSuccess ) scale  = 1;                
                offset   = GDALGetRasterOffset(         hBandSrc, &pbSuccess); if( ! pbSuccess ) offset = 0;                

		GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_tiff_UInt16, pxSizeX, pxSizeY, types, 0, 0);
		for( i = 0; i < (pxSizeX*pxSizeY); i++ ) if ( (double)data_tiff_UInt16[i] != nodata ) data_tiff[i] = ( (float)data_tiff_UInt16[i] - offset ) * scale;
		free(data_tiff_UInt16);

	} else {
		printf("Data type Unknown %s\n", tiff_name);
		return 1;
	}

	GDALClose(hSrcDS);	

	if ( GDALInvGeoTransform(padfGeoTransform, invfGeoTransform) == FALSE ){
	        printf("Problem with inversion of matrix\n");
	        return 1;
	}




	for(i = 0; i < 6; i++) printf("invfGeoTransform[%d]: %f\n", i, invfGeoTransform[i]);

	// ---------------------------------------------------- // 

	int startOffet = ( ( (int)xdim * (int)ydim ) * ldim * time ) + ( ( (int)xdim * (int)ydim ) * altitude );



	for ( i = startOffet, k = 0; i < ( startOffet + ( (int)xdim * (int)ydim) ); i++, k++) data_hit[k] = -1; 

	for ( i = startOffet, k = 0; i < ( startOffet + ( (int)xdim * (int)ydim) ); i++, k++){
		x  = ( k % (int)xdim );
		y  = ( k / (int)xdim );
		GDALApplyGeoTransform( GeoTransform, 	 x,  	y, 	&lon, &lat);
		GDALApplyGeoTransform( invfGeoTransform, lon,  	lat, 	&x, &y);

		if ( (int)x < 0 ) 	   	continue;
		if ( (int)y < 0 ) 	   	continue;
		if ( (int)x >= pxSizeX )   	continue;
		if ( (int)y >= pxSizeY )   	continue;
		j = (int)x + ( (int)y * pxSizeX);
		if ( data_tiff[j] <= 0 )	continue;

		if ( data_hit[k] < 0 ) 	{ data_in[i]  = data_tiff[j]; data_hit[k] = 1; 	}
		else			{ data_in[i] += data_tiff[j]; data_hit[k]++;	}
	}


	for ( i = startOffet, k = 0; i < ( startOffet + ( (int)xdim * (int)ydim) ); i++, k++) if ( data_hit[k] > 0 ) data_in[i] = data_in[i] / (float)data_hit[k]; 


	status = nc_put_var_float(ncid, varid, data_in);
	if(status != NC_NOERR) { printf("nc_put_var_int\n");  return 1; }



	nc_close(ncid);

	printf("Done...\n");	

	return 0;
}
