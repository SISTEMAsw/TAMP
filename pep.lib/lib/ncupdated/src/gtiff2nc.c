#include <stdio.h>
#include <stdlib.h>
#include <netcdf.h>
#include <gdal.h>

#define SUBDATASET "PM10"

int main(int argc, char **argv){
	int i, j, k;
	char	*nc_name	= NULL;
	char	*tiff_name	= NULL;
	char	*aot_name	= NULL;
	char	*coord_name	= NULL;

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
	int	time     	= 0;
	int	altitude 	= 0;



	nc_name		= argv[1];
	tiff_name 	= argv[2];
	aot_name 	= argv[3];
	coord_name	= argv[4];
	time		= atoi(argv[5]); 
	altitude	= atoi(argv[6]);

	status = nc_open(nc_name, NC_WRITE, &ncid);
	if(status != NC_NOERR) { printf("nc_open\n");		return 1; }


	status = nc_inq_varid(ncid, SUBDATASET, &varid);
	if(status != NC_NOERR) { printf("nc_inq_varid\n"); 	return 1; }

	nc_inq_varndims ( ncid, varid, &nd );
	nc_inq_vardimid(  ncid, varid, paDimIds ); paDimIds = (int *)malloc(nd * sizeof(int));
	nc_inq_vardimid(  ncid, varid, paDimIds );



	nc_inq_dimlen ( ncid, paDimIds[nd-1], &xdim );
	nc_inq_dimlen ( ncid, paDimIds[nd-2], &ydim );
	nc_inq_dimlen ( ncid, paDimIds[nd-3], &ldim );
	nc_inq_dimlen ( ncid, paDimIds[nd-4], &tdim );


	data_in = (float *)malloc(sizeof(float) * (int)xdim * (int)ydim * (int)ldim * (int)tdim );
	if(data_in == NULL)    { printf("malloc\n"); 		return 1; }

	printf("Loading NetCDF ...\n");
	status = nc_get_var_float(ncid, varid, data_in);
	if(status != NC_NOERR) { printf("nc_get_var_float\n"); 	return 1; }



	// ---------------------------------------------------- // 
	GDALAllRegister();


	GDALDatasetH	hSrcDS;
	GDALRasterBandH	hBandSrc;
	int		pxSizeX 		= 0;
	int		pxSizeY 		= 0;
	int		types			= 0;
	float		*data_tiff 		= NULL;
	float		*data_aot 		= NULL;
	float		*data_coord[2] 		= { NULL, NULL};
	double 		padfGeoTransform[6] 	= {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
	double 		invfGeoTransform[6] 	= {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
	double 		x, y;

	// ---------------------------------------------------- // 
	printf("Loading new layer ...\n");
	if ( (hSrcDS = GDALOpen( tiff_name, GA_ReadOnly )) == NULL ){
		printf("Unable open src file %s\n", tiff_name);
		return 1;
	}

	pxSizeX  = GDALGetRasterXSize(hSrcDS);
	pxSizeY  = GDALGetRasterYSize(hSrcDS);
	hBandSrc = GDALGetRasterBand( hSrcDS, 1 );
	types	 = GDALGetRasterDataType(hBandSrc);
	data_tiff = (float *)malloc( GDALGetDataTypeSize(types)/8 *  pxSizeX * pxSizeY);
	if(data_tiff == NULL)    { printf("malloc\n");	return 1; }

	GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_tiff, pxSizeX, pxSizeY, types, 0, 0);
	GDALClose(hSrcDS);	

	// ---------------------------------------------------- // 

	printf("Loading coord layer ...\n");
	if ( (hSrcDS = GDALOpen( coord_name, GA_ReadOnly )) == NULL ){
		printf("Unable open src file %s\n", tiff_name);
		return 1;
	}

	pxSizeX  = GDALGetRasterXSize(hSrcDS);
	pxSizeY  = GDALGetRasterYSize(hSrcDS);

	hBandSrc = GDALGetRasterBand( hSrcDS, 1 );
	types	 = GDALGetRasterDataType(hBandSrc);

	data_coord[0] = (float *)malloc( GDALGetDataTypeSize(types)/8 *  pxSizeX * pxSizeY);
	if(data_coord[0] == NULL)    { printf("malloc\n");	return 1; }
	data_coord[1] = (float *)malloc( GDALGetDataTypeSize(types)/8 *  pxSizeX * pxSizeY);
	if(data_coord[1] == NULL)    { printf("malloc\n");	return 1; }

	GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_coord[0], pxSizeX, pxSizeY, types, 0, 0);
	hBandSrc = GDALGetRasterBand( hSrcDS, 2 );
	GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_coord[1], pxSizeX, pxSizeY, types, 0, 0);
	GDALClose(hSrcDS);	

	// ---------------------------------------------------- // 

	printf("Loading AOT layer ...\n");
	if ( (hSrcDS = GDALOpen( aot_name, GA_ReadOnly )) == NULL ){
		printf("Unable open src file %s\n", tiff_name);
		return 1;
	}

	pxSizeX  = GDALGetRasterXSize(hSrcDS);
	pxSizeY  = GDALGetRasterYSize(hSrcDS);

	hBandSrc = GDALGetRasterBand( hSrcDS, 1 );
	types	 = GDALGetRasterDataType(hBandSrc);

	data_aot = (float *)malloc( GDALGetDataTypeSize(types)/8 *  pxSizeX * pxSizeY);
	if(data_aot == NULL)    { printf("malloc\n");	return 1; }

	GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_aot, pxSizeX, pxSizeY, types, 0, 0);

       if ( GDALGetGeoTransform( hSrcDS, padfGeoTransform ) == CE_Failure ){
                printf("Image no transform can be fetched...\n");
		return 1;
        }
	if ( GDALInvGeoTransform(padfGeoTransform,invfGeoTransform) == FALSE ){
	        printf("Problem with inversion of matrix\n");
	        return 3;
	}

	int startOffet = ( ( (int)xdim * (int)ydim ) * ldim * time ) + ( ( (int)xdim * (int)ydim ) * altitude );

	for ( i = startOffet, k = 0; i < ( startOffet + ( (int)xdim * (int)ydim) ); i++, k++){
		GDALApplyGeoTransform( invfGeoTransform, data_coord[1][k], data_coord[0][k], &x, &y);
		if ( (int)x < 0 ) 	   continue;
		if ( (int)y < 0 ) 	   continue;
		if ( (int)x >= pxSizeX )   continue;
		if ( (int)y >= pxSizeY )   continue;
		j = (int)x + ( (int)y * pxSizeX);

		if ( data_aot[j]  <= -9.0  ) continue;
		if ( data_tiff[j] >  500.0 ) continue;

		data_in[i] = data_tiff[j];
		
	}

	
	status = nc_put_var_float(ncid, varid, data_in);
	if(status != NC_NOERR) { printf("nc_put_var_int\n");  return 1; }




	nc_close(ncid);
	GDALClose(hSrcDS);	

	printf("Done...\n");	

	return 0;
}
