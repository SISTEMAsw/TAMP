#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <libgen.h>
#include <sys/stat.h>
#include <sys/types.h>

// GDAL Libraries
#include <gdal.h>
#include <cpl_string.h>
#include <ogr_srs_api.h>
#include <gdalwarper.h>


#define NO_VALUE	200
#define YES_VALUE	0
#define NO_ZONE		-1
#define N_ZONE		0
#define	S_ZONE		1
#define TOBBOX		99999

#define MIN_GRID_STEP	4

#define INPUT_LATLON	1
#define INPUT_PIXEL	2

#define WIN_SEARCH_X	21
#define WIN_SEARCH_Y	21

#define DIST_MAX_FAT	2



double sin1             = 4.84814E-06;
double equatorialRadius = 6378137;
double polarRadius      = 6356752.314;
double k0               = 0.9996;
double A0               = 6367449.146;
double B0               = 16038.42955;
double C0               = 16.83261333;
double D0               = 0.021984404;
double E0               = 0.000312705;




typedef struct COORD{  
	int		toBeProcess;
	double	 	lat;
	double		lon;
	int		lonZone;
	char		latZone;
	struct COORD	*left;
	struct COORD	*right;
	struct COORD	*next;
	struct COORD	*prev;
} COORD; 

//-----------------------------------------------------------------------------------------------------------------

double degreeToRadian(double degree) { return degree * M_PI / 180; }

//-----------------------------------------------------------------------------------------------------------------

int writeTestFileDouble(char *name, double *raster, int x_size, int y_size){
	GDALDatasetH	hDstDS;
	GDALRasterBandH	hBandDst;
	GDALDriverH     hDriver;
	hDriver = GDALGetDriverByName("GTiff");
	hDstDS = GDALCreate( hDriver, name, x_size, y_size, 1, GDT_Float64,    NULL );
        hBandDst = GDALGetRasterBand( hDstDS, 1 );
        GDALRasterIO( hBandDst, GF_Write, 0, 0, x_size, y_size, raster, x_size, y_size, GDT_Float64, 0, 0);
	GDALClose(hDstDS); 
	return 0;
}

//-----------------------------------------------------------------------------------------------------------------

int writeTestFileFloat(char *name, float *raster, int x_size, int y_size){
	GDALDatasetH	hDstDS;
	GDALRasterBandH	hBandDst;
	GDALDriverH     hDriver;
	hDriver = GDALGetDriverByName("GTiff");
	hDstDS = GDALCreate( hDriver, name, x_size, y_size, 1, GDT_Float32,    NULL );
        hBandDst = GDALGetRasterBand( hDstDS, 1 );
        GDALRasterIO( hBandDst, GF_Write, 0, 0, x_size, y_size, raster, x_size, y_size, GDT_Float32, 0, 0);
	GDALClose(hDstDS); 
	return 0;
}

//-----------------------------------------------------------------------------------------------------------------

int writeTestFileByte(char *name, unsigned char *raster, int x_size, int y_size){
	GDALDatasetH	hDstDS;
	GDALRasterBandH	hBandDst;
	GDALDriverH     hDriver;
	hDriver = GDALGetDriverByName("GTiff");
	hDstDS = GDALCreate( hDriver, name, x_size, y_size, 1, GDT_Byte,    NULL );
        hBandDst = GDALGetRasterBand( hDstDS, 1 );
        GDALRasterIO( hBandDst, GF_Write, 0, 0, x_size, y_size, raster, x_size, y_size, GDT_Byte, 0, 0);
	GDALClose(hDstDS); 
	return 0;
}

//-----------------------------------------------------------------------------------------------------------------

int OLS(float *x, float *y, int size){
	int 	i, num;
	float 	x_sum 	= 0.0f,	y_sum 	= 0.0f,	xy_sum = 0.0f,	x2_sum = 0.0f;
	float 	m	= 0.0f, q	= 0.0f;

	x_sum = y_sum = xy_sum = x2_sum = num = 0.0f;

	for( i = 0; i < size; i++){
		x_sum 	+= x[num];
		y_sum 	+= y[num];
		xy_sum 	+= (x[num] * y[num]);
		x2_sum 	+= (x[num] * x[num]);
		num++;

	}

	m = ( (x_sum * y_sum)  - ((float)num * xy_sum) 	) / ( (x_sum * x_sum) - ((float)num * x2_sum) );
	q = ( (x_sum * xy_sum) - (x2_sum * y_sum) 	) / ( (x_sum * x_sum) - ((float)num * x2_sum) );
	for( i = 0; i < size; i++){
		y[i] = m * x[i] + q;
		
	}

	return(0);
}

//-----------------------------------------------------------------------------------------------------------------

double interpolate2D(double wi, double wj, double x00, double x10, double x01, double x11){
     return x00 + wi * (x10 - x00) + wj * (x01 - x00) + wi * wj * (x11 + x00 - x01 - x10);
}

//-----------------------------------------------------------------------------------------------------------------

void decode_tiepoint(	double	*sa_beg, 
			double	*sa_end,
			int 	samples_per_tie_pt,
			int 	num_elems,
			int 	longi_flag, 
			int 	offset_x, 
			double 	scan_offset_x,
			double 	y_mod,
			int 	raster_width, 
			int 	s_x, 
			double	*raster_buffer, 
			int 	raster_pos) {


	int	ix;
	double 	x_mod;
	int 	x_knot;
	int 	intersection = 0;
	double	circle;
	double 	half_circle; 
	double 	null_point;

	int 	EPR_LONGI_ABS_MAX = 180;
	int	EPR_LONGI_ABS_MIN = -180;
	
	circle = EPR_LONGI_ABS_MAX - EPR_LONGI_ABS_MIN;
	half_circle = 0.5 * circle; 
	null_point  = 0.5 * (EPR_LONGI_ABS_MAX + EPR_LONGI_ABS_MIN);
	
	for (ix = offset_x; ix < offset_x + raster_width; ix += s_x) {
		x_mod = (ix - scan_offset_x) / samples_per_tie_pt;
		if (x_mod >= 0.0){
			x_knot = (int)floor(x_mod);
			if (x_knot >= num_elems - 1) {
				x_knot = num_elems - 2;
		        }
		} else {
			x_knot = (int)0;
		}
		x_mod -= x_knot;
	
		if (longi_flag == 1) {
			if (fabs((double)(sa_beg[x_knot + 1] - sa_beg[x_knot])) > half_circle ||
	        		fabs((double)(sa_beg[x_knot] - sa_end[x_knot])) > half_circle ||
	        		fabs((double)(sa_end[x_knot] - sa_end[x_knot + 1])) > half_circle ||
	        		fabs((double)(sa_end[x_knot + 1] - sa_beg[x_knot + 1])) > half_circle) {
				intersection = 1;
				if (sa_beg[x_knot] < (double)null_point) {
					sa_beg[x_knot] += circle;
	    			}
				if (sa_beg[x_knot + 1] < (double)null_point) {
	       				sa_beg[x_knot + 1] += circle;
	      			}
	      			if (sa_end[x_knot] < (double)null_point) {
	         			sa_end[x_knot] += circle;
	     			}
	       			if (sa_end[x_knot + 1] < (double)null_point) {
	        			sa_end[x_knot + 1] += circle;
	       			}
	       		}
	    	} else {
	        	intersection = 0;
	    	}
		raster_buffer[raster_pos] = interpolate2D(x_mod, y_mod,
	                                                  sa_beg[x_knot], sa_beg[x_knot + 1],
	                                                  sa_end[x_knot], sa_end[x_knot + 1]);
	    	if (longi_flag == 1 && 
	        	intersection == 1 && 
	        	raster_buffer[raster_pos] > EPR_LONGI_ABS_MAX) {
	        	raster_buffer[raster_pos] -= circle;
	   	}
	 	raster_pos++;
	}
}

//-----------------------------------------------------------------------------------------------------------------

int makeTreeDirectory(char *old_file_path, float lat, float lon, char *tile_time, char **new_file_path){

	char	latstr[7]	= {};
	char	lonstr[8]	= {};
	char	year[5]		= {};
	char	tmp[255]	= {};
	char	path[255]	= {};
	char	name[255]	= {};
	char	output[255]	= {};
	char	*file_out	= NULL;


	if ( tile_time == NULL ) return 1;


	// Directory tree for level zero is used also for other levels
	lon = (double)(((int)( lon * 100 ) / 25 ) * 25 ) / 100.0;
	lat = (double)(((int)( lat * 100 ) / 25 ) * 25 ) / 100.0;

	if ( lon == 180.0 ) lon = -180.0;


	if ( lat >= 0.0f )	sprintf(latstr, "+%05.2f",	lat);
	else			sprintf(latstr, "%06.2f",	lat);

	if ( lon >= 0.0f )	sprintf(lonstr, "+%06.2f",	lon);
	else			sprintf(lonstr, "%07.2f",	lon);


	if ( ( file_out = malloc(sizeof(char) * ((int)strlen(old_file_path) + 1 )) ) == NULL ){
                printf ("Malloc error file_out\n");
                exit(4);
	}

	sprintf(file_out, "%s", old_file_path);

	strncpy(year, tile_time, 4);
	strcpy(tmp, file_out);
	sprintf(path, "%s", dirname(file_out));
	sprintf(name, "%s", basename(tmp));


	sprintf(output, "%s/%s", path, latstr );
       	mkdir(output, S_IRWXU | S_IRWXG | S_IRWXO);
	sprintf(output, "%s/%s/%s", path, latstr, lonstr );
       	mkdir(output, S_IRWXU | S_IRWXG | S_IRWXO);
	sprintf(output, "%s/%s/%s/%s", path, latstr, lonstr, year );
       	mkdir(output, S_IRWXU | S_IRWXG | S_IRWXO);

	sprintf(output, "%s/%s/%s/%s/%s", path, latstr, lonstr, year, name );

        if ( ( *new_file_path = malloc(sizeof(char) * ((int)strlen(output) + 1 )) ) == NULL ){
                printf ("Malloc error new_file_path\n");
                exit(4);
        }	
	sprintf(*new_file_path, "%s", output);

	return 1;
}


//-----------------------------------------------------------------------------------------------------------------

float getTimeForLine(char *start, char *end, int num_line){
	int 	i;
	int	sec_start	= 0;
	int	sec_end		= 0;
	char	*start_tmp	= NULL;
	char	*end_tmp 	= NULL;
	char	*tok		= NULL;
	int	time_value[3]	= { 0, 0, 0 };
	float	time4line	= 0.0f;;

	// Safe original string...
        if ( ( start_tmp = malloc(sizeof(char) * 9) ) == NULL ){
                printf ("Malloc error start_tmp\n");
                exit(4);
        }
	
	switch( (int)strlen(start) ){
		case 8:
			strcpy(start_tmp, start);
			break;
		case 19:
			strcpy(start_tmp, &start[11]);
			break;
		default:
			printf("Invalid start time format!\n");
			exit(5);

	}

        if ( ( end_tmp = malloc(sizeof(char) * (strlen(end) + 1 )) ) == NULL ){
                printf ("Malloc error end_tmp\n");
                exit(4);
        }	
	strcpy(end_tmp, end);

	// Parstin start time
	for( i = 0, tok = strtok(start_tmp, ":");  tok !=  NULL; tok = strtok(NULL, ":"), i++ ){
		time_value[i] = atoi(tok);

	}
	// test input value
	if (	( i != 3 )			||
		( time_value[0] > 23 )		||
		( time_value[0] < 0 )		|| 
		( time_value[1] > 59 )		||
		( time_value[1] < 0 )		|| 
		( time_value[2] > 59 )		||
		( time_value[2] < 0 )		){

		printf("Invalid start time format!\n");
		exit(5);
	}

	sec_start = time_value[0] * 3600 + time_value[1] * 60 + time_value[2];

	// Parstin end time
	for( i = 0, tok = strtok(end_tmp, ":");  tok !=  NULL; tok = strtok(NULL, ":"), i++ ){
		time_value[i] = atoi(tok);

	}
	// test input value
	if (	( i != 3 )			||
		( time_value[0] > 23 )		||
		( time_value[0] < 0 )		|| 
		( time_value[1] > 59 )		||
		( time_value[1] < 0 )		|| 
		( time_value[2] > 59 )		||
		( time_value[2] < 0 )		){

		printf("Invalid end time format!\n");
		exit(5);
	}

	sec_end = time_value[0] * 3600 + time_value[1] * 60 + time_value[2];
	if ( sec_start > sec_end ) sec_end += 3600 * 24;

	time4line = (float)( sec_end - sec_start ) / num_line;
	return(time4line);
}

//-----------------------------------------------------------------------------------------------------------------

int getTleTime(char *start, float   time4line, int lineoffset, char *output){
	int 	i;
	int	k		= 0;

	float	h		= 0.0f;
	float	m		= 0.0f;
	float	s		= 0.0f;	
	float	D		= 0.0f;
	float	Y		= 0.0f;
	float	M		= 0.0f;	
	float	timeoffset	= 0.0f;

	int	sec_start	= 0;
	char	*tok		= NULL;
	char	*start_tmp	= NULL;
	int	time_value[6]	= { 1970, 1, 1, 0, 0, 0 };
	int	month_leght[12]	= { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };


	// Safe original string...
        if ( ( start_tmp = malloc(sizeof(char) * ((int)strlen(start) + 1 ) ) ) == NULL ){
                printf ("Malloc error start_tmp\n");
                exit(4);
        }
	
	strcpy(start_tmp, start);

	switch( (int)strlen(start) ){
		case 8:
			k = 3;
			break;
		case 19:
			k = 0;
			break;
		default:
			printf("Invalid start time format!\n");
			exit(5);

	}


	// Parstin start time
	for( i = k, tok = strtok(start_tmp, ":");  tok !=  NULL; tok = strtok(NULL, ":"), i++ ){
		time_value[i] = atoi(tok);

	}

	if (( (time_value[0] % 4 == 0) && (time_value[0] % 100 != 0) ) || time_value[0] % 400 == 0 ) month_leght[1]++;
	
	if (	
		( time_value[1] > 12 )					||
		( time_value[1] < 1 )					|| 
		( time_value[2] > month_leght[time_value[1]-1] )	||
		( time_value[2] < 1 )					||

		( time_value[3] > 23 )					||
		( time_value[3] < 0 )					|| 
		( time_value[4] > 59 )					||
		( time_value[4] < 0 )					|| 
		( time_value[5] > 59 )					||
		( time_value[5] < 0 )					){

		printf("Invalid start time format!\n");
		exit(5);
	}

	sec_start = time_value[3] * 3600 + time_value[4] * 60 + time_value[5];	
	timeoffset = (float)sec_start + ((float)lineoffset * time4line);

	h = (timeoffset/3600.0f);

	m = (h -(float)(int)h) * 60.0f;
	s = (m -(float)(int)m) * 60.0f;
	h = (int)h;
	m = (int)m;
	s = ( (s-(float)(int)s) < 0.5f ) ? (int)s : (int)(s+0.5f);
	Y = (float)time_value[0];
	M = (float)time_value[1];
	D = (float)time_value[2];
	
	if ( s >= 60.0f ) { s = s - 60.0f; m = m + 1.0f; }
	if ( m >= 60.0f ) { m = m - 60.0f; h = h + 1.0f; }
	if ( h >= 24.0f ) { h = h - 24.0f; D = D + 1.0f; }

	if ( D > (float)month_leght[(int)M-1] )	{ D = 1.0f; M = M + 1.0f; }
	if ( M > 12.0f )			{ M = 1.0f; Y = Y + 1.0f; }

	switch (k){
		case 3:
			sprintf(output,"%02d%02d%02d", (int)h,(int)m,(int)s );
			break;
		case 0:
			sprintf(output,"%04d%02d%02d_%02d%02d%02d", (int)Y,(int)M,(int)D,(int)h,(int)m,(int)s );
			break;
		default:
			return 1;	

	}
	return 0;
}

//-----------------------------------------------------------------------------------------------------------------

double deg2rad(double alpha){
	return ( alpha * ( M_PI / 180.0 ));
}

//-----------------------------------------------------------------------------------------------------------------

double distVincenty(double lat1, double lon1, double lat2, double lon2) {
	double	a		= 6378137;
	double	b		= 6356752.3142;
	double	f		= 1.0 / 298.257223563;  // WGS-84 ellipsiod
	double	iterLimit	= 100.0;

	double	lambdaP		= 0.0;
	double	L		= 0.0;
	double	U2		= 0.0;
	double	sinU1		= 0.0;
	double	U1		= 0.0;
	double	cosU1		= 0.0;
	double	sinU2		= 0.0;
	double	cosU2		= 0.0;
	double	lambda		= 0.0;
	double	sinLambda	= 0.0;
	double	cosLambda	= 0.0;
	double	sinSigma	= 0.0;
	double	cosSigma	= 0.0;
	double	sigma		= 0.0;
	double	sinAlpha	= 0.0;
	double	cosSqAlpha	= 0.0;
	double	cos2SigmaM	= 0.0;
	double	C		= 0.0;
	double	A		= 0.0;
	double	uSq		= 0.0;
	double	B		= 0.0;
	double	deltaSigma	= 0.0;
	double	s		= 0.0;



	L	= deg2rad(lon2-lon1);
	U1	= atan( (1.0 - f) * tan(deg2rad(lat1)) );
	U2	= atan( (1.0 - f) * tan(deg2rad(lat2)) );
	sinU1	= sin(U1);
	cosU1 	= cos(U1);
	sinU2	= sin(U2);
	cosU2	= cos(U2);
	lambda	= L;

	do {
		sinLambda	= sin(lambda);
		cosLambda	= cos(lambda);
		sinSigma	= sqrt( (cosU2*sinLambda) * (cosU2*sinLambda) + (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda));
		if ( sinSigma == 0.0 ) return (0.0);  // co-incident points

		cosSigma	= sinU1*sinU2 + cosU1*cosU2*cosLambda;
		sigma		= atan2(sinSigma, cosSigma);
		sinAlpha	= cosU1 * cosU2 * sinLambda / sinSigma;
		cosSqAlpha 	= 1.0 - sinAlpha*sinAlpha;
		if ( cosSqAlpha == 0.0 ) cos2SigmaM	= 0.0;
		else			 cos2SigmaM	= cosSigma - 2.0*sinU1*sinU2/cosSqAlpha;

		C		= f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha));
		lambdaP		= lambda;
		lambda		= L + (1-C) * f * sinAlpha * (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)));
	} while ( (abs(lambda-lambdaP) > 1e-12) && (--iterLimit>0) );

	if ( iterLimit == 0 ) return (-1.0);  // formula failed to converge

	uSq		= cosSqAlpha * (a*a - b*b) / (b*b);
	A		= 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)));
	B		= uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)));
	deltaSigma 	= B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM) - B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)));
	s		= b*A*(sigma-deltaSigma);
	s		= ((double)(int)(s * 1000.0 )) / 1000.0; // round to 1mm precision
	return(s);
}


//-----------------------------------------------------------------------------------------------------------------

int fromLatLongtoZoneId(double lat, double lon, double COORD_STEP, int WIN_SIZE_X, int WIN_SIZE_Y){
	int zoneID = 0;

	if ( lon == 180.0 ) lon = -180.0;
	if ( lon >  180.0 ) lon -= 360.0;

	zoneID = (int)  ( (90.0 - lat)/( COORD_STEP * WIN_SIZE_Y ) * ( 360.0 / ( COORD_STEP * WIN_SIZE_Y )) 	) + 
			( (180.0+ lon)/( COORD_STEP * WIN_SIZE_X ) 						) + 1;

	return (zoneID);
}

int fromZoneIdtoLatLon(int zoneId){
	float	lat = 0.0;
	float	lon = 0.0;

	lat = (90 -     ( (float)((zoneId-1) / 1440 ) ) * 0.25            );
	lon = (         ( (float)((zoneId-1) % 1440 ) ) * 0.25 - 180      );
	fprintf(stderr, "%f %f\n", lat,  lon);

	return 0;
}

//-----------------------------------------------------------------------------------------------------------------

double distAprox(double lat1, double lon1, double lat2, double lon2) {
        double	R	= 6372.795477598;
	double	dLat	= 0.0;
	double	dLon	= 0.0;
	double	a	= 0.0;
	double	c	= 0.0;

	dLat = (lat2-lat1) * ( M_PI / 180.0 );
	dLon = (lon2-lon1) * ( M_PI / 180.0 ); 

	a	= sin(dLat/2.0) * sin(dLat/2.0) + cos(lat1 * ( M_PI / 180.0 )) * cos(lat2 * ( M_PI / 180.0 )) * sin(dLon/2.0) * sin(dLon/2.0); 
	c 	= 2.0 * atan2(sqrt(a), sqrt(1-a)); 

	return( R * c  * 1000.0);
}


//-----------------------------------------------------------------------------------------------------------------

double closeEarthFixed(double coord, int step, int round){
	// round == 1 up
	// round == 0 down
	int	i;
	double	coord_int	= 0.0;
	double	grid_dim	= 0.0;
	double	coord_1		= 0.0;
	double	coord_2		= 0.0;
	double	coord_new	= 0.0;

	if (( round < 0 ) || ( round > 1 ) ) round = 0;

	coord_int 	= (double)((int)coord);
	grid_dim	= 1.0 / (double)step;

	if ( coord > 0.0 ){
		for ( i = 0; i < step; i ++ ){
			coord_1 = coord_int + ((double)i	* grid_dim);
			coord_2 = coord_int + ((double)(i+1)	* grid_dim);
			if (( coord >= coord_1 ) && ( coord < coord_2 )){
				if ( round == 0) coord_new = coord_1; 
				if ( round == 1) coord_new = coord_2;
				break;
			}
		}
	}else{	
		for ( i = 0; i < step; i ++ ){
			coord_1 = coord_int - ( (double)(i+1)	* grid_dim);
			coord_2 = coord_int - ( (double)i	* grid_dim);
			if (( coord >= coord_1 ) && ( coord <= coord_2 )){
				if ( round == 0) coord_new = coord_1; 
				if ( round == 1) coord_new = coord_2;
				break;
			}
		}
	}
	return (coord_new);
}

//-----------------------------------------------------------------------------------------------------------------

int pnpoly(int nvert, double *vertx, double *verty, double testx, double testy){
	int i, j, c = 0;
	for (i = 0, j = nvert-1; i < nvert; j = i++) {
		if ( ((verty[i]>testy) != (verty[j]>testy)) &&  (testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i]) )  c = !c;
	}
	return c;
}

//-----------------------------------------------------------------------------------------------------------------

double bearing( double lon1, double lat1, double lon2, double lat2){
        // See T. Vincenty, Survey Review, 23, No 176, p 88-93,1975.
        // Convert to radians.
	double radianPerdegrees =  M_PI / 180.0;
	double angle		= 0.0;

	lat1 = lat1 * radianPerdegrees;
	lon1 = lon1 * radianPerdegrees;
	lat2 = lat2 * radianPerdegrees;
	lon2 = lon2 * radianPerdegrees;
	// Compute the angle.
	angle = - atan2( sin( lon1 - lon2 ) * cos( lat2 ), cos( lat1 ) * sin( lat2 ) - sin( lat1 ) * cos( lat2 ) * cos( lon1 - lon2 ) );
	if ( angle < 0.0 ) angle  += M_PI * 2.0;
	
	// And convert result to degrees.
	angle = angle * 180.0 / M_PI;
	return angle;
}



//-----------------------------------------------------------------------------------------------------------------



int decimalCounter(double num){
	int	i;
	int	s 		= 0;
	int	e 		= 0;
	char 	tmp[256] 	= "";

	sprintf(tmp,"%.50f", num);
	for(i = strlen(tmp) - 1; i > -1 ; i--){
		if (( s == 0 ) && ( tmp[i] != '0' )) 	s = i;
		if ( tmp[i] == '.' ) 		{	e = i; break; }
	}
	return (s-e);
}


//-----------------------------------------------------------------------------------------------------------------

int getEasting(double latitude, double longitude, double *easting, double *northing){
        latitude        = degreeToRadian(latitude);

        double var1     = 0.0;

	if (longitude < 0.0)    var1 = ((int) ((180 + longitude) / 6.0)) + 1;
	else                    var1 = ((int) (longitude / 6)) + 31;

        double var2     = (6 * var1) - 183;
        double var3     = longitude - var2;
        double p        = var3 * 3600 / 10000;
        double e        = sqrt(1 - pow(polarRadius / equatorialRadius, 2));
        double e1sq     = e * e / (1 - e * e);
        double nu       = equatorialRadius / pow(1 - pow(e * sin(latitude), 2), (1 / 2.0));
        double S        = A0 * latitude - B0 * sin(2 * latitude) + C0 * sin(4 * latitude) - D0 * sin(6 * latitude) + E0 * sin(8 * latitude);
        double K1       = S * k0;
        double K2       = nu * sin(latitude) * cos(latitude) * pow(sin1, 2) * k0 * (100000000) / 2;
        double K3       = ((pow(sin1, 4) * nu * sin(latitude) * pow(cos(latitude), 3)) / 24) * (5 - pow(tan(latitude), 2) + 9 * e1sq * pow(cos(latitude), 2) + 4 * pow(e1sq, 2) * pow(cos(latitude), 4)) * k0 * (10000000000000000L);
        double K4       = nu * cos(latitude) * sin1 * k0 * 10000;
        double K5       = pow(sin1 * cos(latitude), 3) * (nu / 6) * (1 - pow(tan(latitude), 2) + e1sq * pow(cos(latitude), 2)) * k0 * 1000000000000L;

        *easting        = 500000 + (K4 * p + K5 * pow(p, 3));
        *northing       = K1 + K2 * p * p + K3 * pow(p, 4);

        return (int)var1;
}

//-----------------------------------------------------------------------------------------------------------------

char getLatZone(double latitude){
        int     i;
        int     latIndex                = -2;
	//int	lat = (int)latitude;
        char    negLetters[11]          = { 'A', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M' };
        char    posLetters[11]          = { 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z' };
        int	posDegrees[11]          = {   0,   8,  16,  24,  32,  40,  48,  56,  64,  72, 84  };
        int	negDegrees[11]          = { -90, -84, -72, -64, -56, -48, -40, -32, -24, -16, -8  };

        if (latitude >= 0){
                for ( i = 0; i < 11; i++){
                        if (latitude == posDegrees[i])       { latIndex = i;         break; }
                        if (latitude >  posDegrees[i])                               continue;
                        else        		             { latIndex = i - 1;     break; }

                }
        }else{
                for ( i = 0; i < 11; i++){
                        if (latitude == negDegrees[i])       { latIndex = i;         break; }
                        if (latitude <  negDegrees[i])       { latIndex = i - 1;     break; }
                        else        		                                     continue;

                }

        }

        if (latIndex == -1) latIndex = 0;
        if (latIndex == -2) latIndex = 10;

        if ( latitude >= 0 ) 	return posLetters[latIndex];
        else         		return negLetters[latIndex];

}

//-----------------------------------------------------------------------------------------------------------------


int getLongZone(double longitude){
        double longZone = 0;

        if (longitude < 0.0 )   longZone = ((180.0 + longitude) / 6) + 1;
        else                    longZone = (longitude / 6) + 31;

        return (int)longZone;
}

//-----------------------------------------------------------------------------------------------------------------

double getLatZoneDegree(char letter){
        int i;
        char    letters[22] = { 'A', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M','N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z' };
        int     degrees[22] = { -90, -84, -72, -64, -56, -48, -40, -32, -24, -16,  -8,  0,   8,  16,  24,  32,  40,  48,  56,  64,  72,  84 };

        for (i = 0; i < 22 ; i++) if (letters[i] == letter) return (double)degrees[i];

        return -100;
}

//-----------------------------------------------------------------------------------------------------------------

char getHemisphere(char latZone){
        int i;
        char southernHemisphere[12]     = "ACDEFGHJKLM";
        char hemisphere                 = 'N';
        for (i = 0; i < strlen(southernHemisphere); i++) if ( southernHemisphere[i] == latZone ) { hemisphere = 'S'; break; }

        return hemisphere;
}

//-----------------------------------------------------------------------------------------------------------------

char getDigraph1(int longZone, double easting){
        int     a1               = longZone;
        double  a2              = 8 * ((a1 - 1) % 3) + 1;
        double  a3              = easting;
        double  a4              = a2 + ((int) (a3 / 100000)) - 1;
        char    digraph1[25]    = { '\0', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z' };


        return digraph1[(int)floor(a4)];

}

//-----------------------------------------------------------------------------------------------------------------

char getDigraph2(int longZone, double northing){
        int     a1              = longZone;
        double  a2              = 1 + 5 * ((a1 - 1) % 2);
        double  a3              = northing;
        double  a4              = (a2 + ((int) (a3 / 100000)));
        char    digraph2[21]    = { 'V', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K',  'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V' };

        a4 = ( (int)(a2 + ((int) (a3 / 100000.0))) % 20 ) + (a2 + ((int) (a3 / 100000.0))) - (double)(int)(a2 + ((int) (a3 / 100000.0)));
        a4 = floor(a4);
        if (a4 < 0) a4 = a4 + 19;

        return digraph2[(int)floor(a4)];

}

//-----------------------------------------------------------------------------------------------------------------



int shiftUTMzone(double f,double f1, double j, double *northing, double *easting, double var1) {
	double d = 0.99960000000000004;
	double d1 = 6378137;
	double d2 = 0.0066943799999999998;
	
	double d4 = (1 - sqrt(1-d2))/(1 + sqrt(1 - d2));
	double d15 = f1 - 500000;
	double d16 = f;
	double d11 = ((j - 1) * 6 - 180) + 3;
	
	double d3 = d2/(1 - d2);
	double d10 = d16 / d;
	double d12 = d10 / (d1 * (1 - d2/4 - (3 * d2 *d2)/64 - (5 * pow(d2,3))/256));
	double d14 = d12 + ((3*d4)/2 - (27*pow(d4,3))/32) * sin(2*d12) + ((21*d4*d4)/16 - (55 * pow(d4,4))/32) * sin(4*d12) + ((151 * pow(d4,3))/96) * sin(6*d12);
	double d5 = d1 / sqrt(1 - d2 * sin(d14) * sin(d14));
	double d6 = tan(d14)*tan(d14);
	double d7 = d3 * cos(d14) * cos(d14);
	double d8 = (d1 * (1 - d2))/pow(1-d2*sin(d14)*sin(d14),1.5);
	
	double d9 = d15/(d5 * d);
	double d17 = d14 - ((d5 * tan(d14))/d8)*(((d9*d9)/2-(((5 + 3*d6 + 10*d7) - 4*d7*d7-9*d3)*pow(d9,4))/24) + (((61 +90*d6 + 298*d7 + 45*d6*d6) - 252*d3 -3 * d7 *d7) * pow(d9,6))/720); 
	d17 = d17 * 180 / M_PI;
	double d18 = ((d9 - ((1 + 2 * d6 + d7) * pow(d9,3))/6) + (((((5 - 2 * d7) + 28*d6) - 3 * d7 * d7) + 8 * d3 + 24 * d6 * d6) * pow(d9,5))/120)/cos(d14);
	d18 = d11 + d18 * 180 / M_PI;
	
	
	
	double latitude  = d17;
	double longitude = d18;

        latitude        = degreeToRadian(latitude);

        double var2     = (6 * var1) - 183;
        double var3     = longitude - var2;
        double p        = var3 * 3600 / 10000;
        double e        = sqrt(1 - pow(polarRadius / equatorialRadius, 2));
        double e1sq     = e * e / (1 - e * e);
        double nu       = equatorialRadius / pow(1 - pow(e * sin(latitude), 2), (1 / 2.0));
        double S        = A0 * latitude - B0 * sin(2 * latitude) + C0 * sin(4 * latitude) - D0 * sin(6 * latitude) + E0 * sin(8 * latitude);
        double K1       = S * k0;
        double K2       = nu * sin(latitude) * cos(latitude) * pow(sin1, 2) * k0 * (100000000) / 2;
        double K3       = ((pow(sin1, 4) * nu * sin(latitude) * pow(cos(latitude), 3)) / 24) * (5 - pow(tan(latitude), 2) + 9 * e1sq * pow(cos(latitude), 2) + 4 * pow(e1sq, 2) * pow(cos(latitude), 4)) * k0 * (10000000000000000L);
        double K4       = nu * cos(latitude) * sin1 * k0 * 10000;
        double K5       = pow(sin1 * cos(latitude), 3) * (nu / 6) * (1 - pow(tan(latitude), 2) + e1sq * pow(cos(latitude), 2)) * k0 * 1000000000000L;

        *easting        = 500000 + (K4 * p + K5 * pow(p, 3));
        *northing       = K1 + K2 * p * p + K3 * pow(p, 4);


	
	return 0;
}
   
//-----------------------------------------------------------------------------------------------------------------




int main(int argc, char **argv){
	// Cursors variables
	int		i, j, k, x, y, z, x_i, y_i;


	GDALDatasetH    hSrcDS, hDstDS, hSrcTiff;
	GDALDriverH     hDriver;
	GDALRasterBandH hBandSrc,hBandDst;
	char            *pszTargetSRS		= NULL;
	double          padfGeoTransform[6]	= {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
	double          gridGeoTransform[6]	= {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};	
    GDAL_GCP	*pasGCPList      	= NULL;
    const char      *pszGCPProjection	= NULL;
	char            **papszOptions          = NULL;
	double		COORD_STEP 		= 0.0;
	int		aatsr_mode 		= FALSE;
	int		RAW_OUTPUT 		= FALSE;
	int		BBOX 			= FALSE;
	int		BBOX_GRID		= FALSE;
	int		CROSS_DATE_LINE		= FALSE;
	int		OUTPUT_IN_METERS	= FALSE;
	int		OUTPUT_UTM		= FALSE;
	int		OUTPUT_UTM_ONLY_LON	= FALSE;
	int		CUSTOM_WINDOWS_SIZE	= FALSE;
	int		CUSTOM_DISTANCE		= FALSE;
	float		PIXEL_NOT_FOUND		= 0;
	double		CUSTOM_DISTANCE_SIZE	= 0;
	int		MUST_ONLY_CUT		= FALSE;
    int             nGCPCount		= 0;
	int		INPUT_TYPE 		= 0;
	int		type 			= 0;
	int		size			= 0;
	char		end_coords[2][256]	= {};
	int		index_argv 		= 0;
	int		WIN_SIZE_X 		= 0;
	int		WIN_SIZE_Y 		= 0;
	double		LR_FIX_lat 		= NO_VALUE;
	double		LR_FIX_lon 		= NO_VALUE;
	double          x_near			= 0.0;
	double		y_near			= 0.0;
	double		xdouble			= 0.0;	
	double		ydouble			= 0.0;	

	GByte           *input			= NULL;
	GByte		*output			= NULL;
	GByte		*MGRSbuffer		= NULL;
	GDALColorTableH	hColor			= NULL;


	// Grid MODE MUHAHAHHAHAHA!!!
	int		GRID_MODE		= FALSE;
	int		TREE_CREATION		= FALSE;
	int		STORE_COORDS		= FALSE;
	int		MGRS_MODE		= FALSE;
	int		ZOOM_LEVEL		= -1;
	int		name_tile_decimal	= 0;

	double		MINLAT			= 0.0;
	double		MAXLAT			= 0.0;
	double		MINLON			= 0.0;
	double		MAXLON			= 0.0;
	double		MINN			= 0.0;
	double		MAXN			= 0.0;
	double		MINE			= 0.0;
	double		MAXE			= 0.0;


	double		fi, fj;
	char		*good_tile		= NULL;

	COORD		*UL_array = NULL, *UP_cursor = NULL;
	COORD		*GT_array = NULL, *GT_cursor = NULL, *GT_head = NULL;


	int		zoneID 		= 0;
	char		*date_start 	= NULL;
	char		*date_end 	= NULL;
	double		time4line 	= 0.0;
	char		*tile_time	= NULL;

	
	int 		pxSizeX 	= 0;
	int		pxSizeY 	= 0;

	int		search_win[2]	= { 0, 0 };
	int		x_win		= 0, 	y_win		= 0,	i_win 		= 0;
	int		x_win_UL	= 0,	y_win_UL	= 0,	x_win_LR	= 0,	y_win_LR = 0;


	int		num_near	= 0;
	int		*near_list	= NULL;

	double		dfGCPPixelOffsetLat = 0.0, dfGCPPixelOffsetLon = 0.0;

	double		*weigh		= NULL,	*dist		= NULL, dist_tot	= 0.0;
	double		FIX_dist	= 0.0,	FIX_new_dist	= 0.0,	dist_avg	= 0.0;
	double		*dist_max	= NULL;

	int		index_remap	= 0,	remap_near	= 0;
	int		blank_pix_cnt	= 0;


	int		BLANK_IMAGE_SKIP	= FALSE;
	double		BLANK_IMAGE_SKIP_VALUE	= 0.0;
	double		coord_step_lat		= 0.0;
	double		coord_step_lon		= 0.0;

	double		**tie_point_lat 	= NULL;
	double		**tie_point_lon		= NULL;
	double		point_y			= 0.0;
	int		*tie_point_y		= NULL;

	double		FIX_lat			= NO_VALUE;
	double		FIX_lon			= NO_VALUE;
	double		lat			= 0.0;
	double		lon			= 0.0;

	char 		*file_in	= NULL;
	char		*file_out	= NULL;
	char		*file_out_tree	= NULL;
	char		*file_pts	= NULL;
	char		*file_post	= NULL;
	char		*file_tiff	= NULL;
	FILE		*fraw		= NULL;
	FILE		*fp 		= NULL;

	char		line[255]	= {};
	char		str[255]	= {};
	char		tmp[255]	= {};

	int		count		= 0;
	int		zone		= NO_ZONE;
	int		NSzone		= N_ZONE;
	fpos_t		*pos		= NULL;
	double		x_gcp		= 0.0;
	double		y_gcp		= 0.0; 
	double		lat_gcp		= 0.0; 
	double		lon_gcp		= 0.0;
	double		lat_avg_1	= 0.0;
	double		lat_avg_2	= 0.0;
	double		lon_avg_1	= 0.0;
	double		lon_avg_2	= 0.0;
	double          GeoX 		= 0.0;	
	double		GeoY 		= 0.0;

	OGRSpatialReferenceH 		hSourceSRS, hTargetSRS;
	OGRCoordinateTransformationH 	hCT = NULL;

	int		GeoTransform 	= TRUE;
	int		pbNorth		= 0;

	float		*tiff_lat	= NULL;
	float		*tiff_lon	= NULL;

	int		tie_for_line	= 0;
	int		tie_dist_line	= 0;

	double		*coordMatrixLat	= NULL;
	double		*coordMatrixLon	= NULL;

	double		*coordMatrix[2]	= {NULL, NULL};		// 0: Lat 1: Lon
	double		coordRemap[2]	= { 0.0, 0.0 };		// 0: Lat 1: Lon
	GByte		*coord_info 	= NULL;
        unsigned char   *matrixLonZone	= NULL;
        char            *matrixLatZone	= NULL;


	unsigned short int *matrixRemap[2] = { NULL, NULL}; // 0: X 1: Y


	char		track_line_key[100]	= {};				
	char		track_line_value[100]	= {};				
	double		*xpoly			= NULL;
	double		*ypoly			= NULL;
        char            **papszMetadata		= NULL;
        int             nCount  		= 0;
        char            *pszKey			= NULL;
        const char      *pszValue;
	int		*track_line		= NULL;
	int		*track_line_x		= NULL;
	int		*track_line_y		= NULL;
	int		*track_line_index	= NULL;
	int		track_line_num		= 0;
	int		TRACK_LINE		= TRUE;	

	//*************************************************************************************************



	// Parsing argumets
	for(index_argv = 1 ; index_argv < argc ; index_argv++){
		if ( argv[index_argv][0] != '-' ) continue;
		switch(argv[index_argv][1]){
			case 'i': // Input file
				file_in		= argv[++index_argv];
				break;
			case 'o': // Output file
				file_out	= argv[++index_argv];
				break;	
			case 'l': // Upper left corner
				FIX_lat 	= atof(argv[++index_argv]);
				FIX_lon 	= atof(argv[++index_argv]);
				break;
			case 's': // Pixel size degree
				COORD_STEP 	= atof(argv[++index_argv]);
				break;
			
			case 'a': // Extra file
				index_argv++;
				file_pts        = argv[index_argv];
				file_tiff       = argv[index_argv];
				break;
			case 'w': // Set searching window
				index_argv++;
				if ( argv[index_argv] == NULL ) break;
				for(i = 0, j = 0, k = 0; i < strlen(argv[index_argv]); i++, k++){
					if ( argv[index_argv][i] == 'x' ){
						argv[index_argv][i] = '\0';
						search_win[0] = atoi(argv[index_argv]);
					}
				}
				search_win[1] = atoi(argv[index_argv]+i);
				CUSTOM_WINDOWS_SIZE = TRUE;
				break;

			case 'e': // End point
				index_argv++;
				for(i = 0; i < 256; i++ ) { end_coords[0][i] = '\0'; end_coords[1][i] = '\0'; }
				for(i = 0, j = 0, k = 0; i < strlen(argv[index_argv]); i++, k++){
					if ( argv[index_argv][i] == ',' ){
						end_coords[j][k] = '\0';
						j++;
						i++;
						k = 0;
						INPUT_TYPE = INPUT_LATLON;
					}
					if ( argv[index_argv][i] == 'x' ){
						end_coords[j][k] = '\0';
						j++;
						i++;
						k = 0;
						INPUT_TYPE = INPUT_PIXEL;
					}
					end_coords[j][k] = argv[index_argv][i];
				}

				if ( INPUT_TYPE == INPUT_PIXEL ){
					WIN_SIZE_X = atoi(end_coords[0]);
					WIN_SIZE_Y = atoi(end_coords[1]);


				}
				if ( INPUT_TYPE == INPUT_LATLON ){
					LR_FIX_lat = atof(end_coords[0]);
					LR_FIX_lon = atof(end_coords[1]);
				}

				break;
			case 'q': // Remapping inside a bounding box
				BBOX = TRUE;
				if (strlen(argv[index_argv]) == 3 ){
					if ( argv[index_argv][2] == 'g' ) BBOX_GRID = TRUE;
				}
				break;

			case 'g': // Grid mode
				GRID_MODE = TRUE;
				break;
			case 'b': // Skip the tiles image all black
				BLANK_IMAGE_SKIP = TRUE;

				if (strlen(argv[index_argv]) >= 3 ) BLANK_IMAGE_SKIP_VALUE = atof( (char *)(argv[index_argv]+2) );
				
				break;
			case 't': // Input file within list of good tiles
				good_tile = argv[++index_argv];
				break;
			case 'r': // Not write geotiff, but only raw raster
				RAW_OUTPUT = TRUE;
				break;
			case 'd': // Input date/time for tile naming
				if (argv[index_argv][2] == 's'){ // can be YYYY:MM:DD:hh:mm:ss or hh:mm:ss 
					date_start = argv[++index_argv];
					break;	
				}
				if (argv[index_argv][2] == 'e'){ //  hh:mm:ss
					date_end = argv[++index_argv];
					break;
				}
				if (argv[index_argv][2] == 't'){ // Create tiles and directory tree 
					TREE_CREATION = TRUE;
					break;
				}
			case 'm': // If input is in meter and you want output georef in meters
				OUTPUT_IN_METERS = TRUE;
				break;

			case 'n': // set not pixel found value
				PIXEL_NOT_FOUND = atof(argv[++index_argv]);
				break;

			case 'z': // grid level
				ZOOM_LEVEL = atoi(argv[++index_argv]);
				break;
			case 'c':
				STORE_COORDS = TRUE;
				break;
				
			case 'u': // Output in UTM
				OUTPUT_UTM = TRUE;

				if 	( argv[index_argv][2] == 't' ) MGRS_MODE 		= TRUE;
				else if ( argv[index_argv][2] == 'l' ) OUTPUT_UTM_ONLY_LON 	= TRUE; 
				
				break;
			case 'f':
				CUSTOM_DISTANCE = TRUE;	
				CUSTOM_DISTANCE_SIZE = atof(argv[++index_argv]);
				break;

			default:
				printf("Invalid optioni (%s)!\n", argv[index_argv]);
				return 1;
		}

	}


	//*************************************************************************************************

	// Autocomputation of resolution for output in utm
	if ( ( OUTPUT_UTM == TRUE ) && ( COORD_STEP == 0.0 )) COORD_STEP = 1.0;

	// Remapping into bouding box
	if ( BBOX == TRUE ){
		FIX_lat		= TOBBOX;
		FIX_lon		= TOBBOX;
		LR_FIX_lat	= TOBBOX;
		LR_FIX_lon	= TOBBOX;
		INPUT_TYPE	= INPUT_LATLON;
		if (( BBOX_GRID == TRUE ) && ( ZOOM_LEVEL >= 0 ))  COORD_STEP = ( 1.0 / pow(2.0, ( 8.0 + (double)ZOOM_LEVEL)) );
	}



	// Set window size like default values if not set in input
	if ( CUSTOM_WINDOWS_SIZE == FALSE ){
		search_win[0] = WIN_SEARCH_X;
		search_win[1] = WIN_SEARCH_Y;
	}
	
	//*************************************************************************************************

	// Test minimum arguments if grid mode is off
	if(( GRID_MODE == FALSE )	&&(
		( file_in  == NULL ) 	||	// input file
		( file_out == NULL )	||	// output file
		( INPUT_TYPE == 0 )	||	// set a input type (lat,lon or XsizexYsize)
		( FIX_lat == NO_VALUE )	||	// Upper left latitude
		( FIX_lon == NO_VALUE )	||	// Upper left longitude
		( COORD_STEP == 0.0f )	||	// Pixel dimention
		( search_win[0] == 0 )	||	// Windows search dimention X
		( search_win[1] == 0 ) )){	// Windows search dimenstin Y

		printf("Usage: remap OPTIONS...\n\n");
		printf("-i	: Input file\n");
		printf("-o	: Output file\n");
		printf("-r	: Raw Output (only raster without format)\n");
		printf("-l	: Upper left corner in lat lon (e.g. -l 44.12 45.11)\n");	
		printf("-e	: Lower right corner in  Lat Lon format (e.g. 44.12,45.11)\n");
		printf("	  or image size format (e.g. 350x400)\n");
		printf("-q	: Remaping inside bounding box, -qg box inEarth Fixed GRID (ignoring options -l, -e)\n");
		printf("-s	: Pixel size in degree (e.g. 0.00390625)\n");
		printf("-m	: Input and output in meters\n");
		printf("-a	: Extra file (.pts or .tiff)\n");
		printf("-b	: Black image or tile skip\n");
		printf("-w	: Set searching window (e.g. 10x10)\n");
		printf("-n	: Set value of not pixel found\n");
		printf("-g	: Earth Fixed GRID MODE... MUAHAHAHAHH!\n");
		printf("-t	: File within list of good tiles in Lat Lon format, sorted by lat\n");
		printf("-z	: Set Earth Fixed Grid Level (active only with -g option, ignoring -s option)\n");
		printf("-c	: Matrix of remapped coordinates\n");
		printf("\n");
		printf("Distance from my house to Castle of Ferrara: %.3f meters\n",  distVincenty(44.805919,  11.742273,  44.837572, 11.619293 ) );
		return 1;

	}
	
	//*************************************************************************************************

	// Test input agurments if grid mode is ON
	if( GRID_MODE == TRUE ){
		printf("***********************************\n");
		printf("*                                 *\n");
		printf("* E A R T H   F I X E D   G R I D *\n");
		printf("*                                 *\n");
		printf("***********************************\n");
		printf("\n");


		if (INPUT_TYPE != INPUT_PIXEL){
			printf("In this mode you must use option -e in image size format (e.g. 35x40)\n");
			return 1;
		}	
		if (( WIN_SIZE_X <= 0 ) || ( WIN_SIZE_Y <= 0 )){
			printf("Invalid size of tile!\n");
			return 1;

		}

		
		if ( ZOOM_LEVEL >= 0 )	COORD_STEP = ( 1.0 / pow(2.0, ( 8.0 + (double)ZOOM_LEVEL)) );

		if ( COORD_STEP == 0.0 ){
			printf("Invalid pixel size!\n");
			return 1;

		}
		/*
		Grid Level	Ref. GSD	Pixel res.	Samples per deg.	Supported sensors
		0		1000		434,84		256			(A)ATSR, MODIS
		1		500		217,42		512			MODIS HKM
		2		250		108,71		1024			MODIS QKM, MERIS
		3		125		54,36		2048			LANDSAT TM TIR
		4		60		27.18		4096			LANDSAT ETM+ TIR
		5		30		13,59		8192			LANDSAT TM/ETM+ MS
		6		15		6,79		16384			LANDSAT ETM+ PAN SPOT5, AVNIR-2
		7		7		3,40		32768			-
		8		3,5		1,70		65536			VHR MS
		9		1,75		0,84		131072			VHR MS
		10		0,8		0,42		262144			VHR PAN
		*/
		if ( ZOOM_LEVEL < 0 ){
			j = (int)(1.0 / COORD_STEP);
			for (i = 0; i < 11 ; i++){
				if( j ==  (int)pow(2,8+i) ) break;
			}
			if ( COORD_STEP !=  ( 1.0 / pow(2.0, ( 8.0 + (double)i)) ) ){
				printf("Warning! I don't find a grid level for your pixel resolution...\n");
				ZOOM_LEVEL = 0;
			}else{
				ZOOM_LEVEL = i;
			}

		}

		for (i = 0; i < strlen(file_out); i++){
			if (file_out[i] == '%' ){
				file_out[i] 	= '\0';
				file_post	= file_out + i + 1;
			}

		}

					printf("Output prefix : %s\n",		file_out);
		if (file_post != NULL)	printf("Output postfix: %s\n",		file_post);
					printf("Tile size     : %dx%d\n",	WIN_SIZE_X, WIN_SIZE_Y);
		if (good_tile != NULL)	printf("Good tiles    : %s\n",		good_tile);
					printf("Grid Level    : %d\n",		ZOOM_LEVEL);	
					printf("Pixel Size    : %.*f\n", 	decimalCounter(COORD_STEP), COORD_STEP );

		if (( RAW_OUTPUT  != TRUE ) && ( TREE_CREATION == TRUE )) TREE_CREATION = FALSE;

		if ( BLANK_IMAGE_SKIP == TRUE )	printf("Skip all black images ... \n");
		if ( TREE_CREATION == TRUE )	printf("Creation of directories tree...\n");

		OUTPUT_IN_METERS	= FALSE; // Disable output in meters
		BBOX                    = FALSE; // Disable bouding box
		BBOX_GRID		= FALSE; 
		CUSTOM_WINDOWS_SIZE     = FALSE; // Disable custom windows size

	}

	//*************************************************************************************************


	// Init GDAL Libraries...
	GDALAllRegister();
	OGRRegisterAll();

	CPLSetErrorHandler(NULL);
	hDriver = GDALGetDriverByName("GTiff"); 



	// Open input image
	if ( (hSrcDS = GDALOpen( file_in, GA_ReadOnly )) == NULL ){
		printf("Unable open src file %s\n", file_in);
		return(1);
	}

	hColor = GDALGetRasterColorTable( GDALGetRasterBand(hSrcDS,1) );
	if( hColor != NULL ){
		hColor = GDALCloneColorTable( hColor );
	}

        hBandSrc	= GDALGetRasterBand( hSrcDS, 1 );
	type		= GDALGetRasterDataType(hBandSrc);
	size		= GDALGetDataTypeSize(type)/8;
        pxSizeX		= GDALGetRasterXSize(hSrcDS);
        pxSizeY		= GDALGetRasterYSize(hSrcDS);

	// Malloc input
	if ( ( input = malloc(size * pxSizeX * pxSizeY) ) == NULL ){
		printf ("Malloc error input\n");
		return(4);
	}
	

	printf("Load file %s in memory...\n", file_in);
        GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, input, pxSizeX, pxSizeY, type, 0, 0);

	printf("Image INFO:\n");
	printf("      Size %dx%d\n", pxSizeX, pxSizeY);



	//*************************************************************************************************
	// Print remapping AOI information

	if ( OUTPUT_IN_METERS == TRUE) printf("Working in meter mode...\n");
	if (( GRID_MODE == FALSE ) &&  ( BBOX != TRUE ) ){
		printf("Input INFO:\n");
		if ( OUTPUT_IN_METERS != TRUE){
								printf("      Upper left : Lat %f / Lon %f\n",	FIX_lat,	FIX_lon		);
			if (INPUT_TYPE == INPUT_LATLON )	printf("      Lower right: Lat %f / Lon %f\n",	LR_FIX_lat,	LR_FIX_lon	);
			if (INPUT_TYPE == INPUT_PIXEL  )	printf("      Dimention  : %dx%d\n", 		WIN_SIZE_X,	WIN_SIZE_Y	);
		}else{
								printf("      Upper left : %fN / %fE\n",	FIX_lat,	FIX_lon		);
			if (INPUT_TYPE == INPUT_LATLON )	printf("      Lower right: %fN / %fE\n",	LR_FIX_lat,	LR_FIX_lon	);
			if (INPUT_TYPE == INPUT_PIXEL  )	printf("      Dimention  : %dx%d\n",		WIN_SIZE_X,	WIN_SIZE_Y	);
		}
	
	}


	//*************************************************************************************************


	if(( GRID_MODE == TRUE ) && ( date_start != NULL ) && ( date_end != NULL )){
		time4line = getTimeForLine(date_start, date_end, pxSizeY);
		printf("Start time: %s, End time: %s\n", date_start, date_end);
		printf("Time of one line: %f\n", time4line);

	        switch( (int)strlen(date_start) ){
	                case 8:
				if ( ( tile_time = (char *)malloc(sizeof(char) * 7 ) ) == NULL ){
					printf ("Malloc error tile_time\n");
					return(4);
				}
      	 	                break;
        	        case 19:
				if ( ( tile_time = (char *)malloc(sizeof(char) * 16 ) ) == NULL ){
					printf ("Malloc error tile_time\n");
					return(4);
				}
        	                break;
        	        default:
        	                printf("Invalid start time format!\n");
        	                return 5;
		}

	}

	//*************************************************************************************************

	// Malloc latitude
	if ( ( coordMatrix[0] = (double *)malloc(sizeof(double) * pxSizeX * pxSizeY) ) == NULL ){
		printf ("Malloc error coordMatrix[0]\n");
		return 4;
	}
	// Malloc longitude
	if ( ( coordMatrix[1] = (double *)malloc(sizeof(double) * pxSizeX * pxSizeY) ) == NULL ){
		printf ("Malloc error coordMatrix[1]\n");
		return 4;
	}
	// Malloc coord_info raster (where i have geoinfo or not)
	if ( ( coord_info = (GByte *)malloc(sizeof(GByte) * pxSizeX * pxSizeY) ) == NULL ){
		printf ("Malloc error coord_info\n");
		return 4;
	}
	// Malloc raster of threshold for remap
	if ( ( dist_max = (double *)malloc(sizeof(double) * pxSizeX * pxSizeY) ) == NULL ){
		printf ("Malloc error dist_max\n");
		return 4;
	}


	//*************************************************************************************************

	printf("- Extration GCPs section -\n");
        pszTargetSRS = (char *)GDALGetProjectionRef( hSrcDS );
	if ( pszTargetSRS == NULL ){
		printf("Image without projection definition...\n");
	}

        if ( GDALGetGeoTransform( hSrcDS, padfGeoTransform ) == CE_Failure ){
		printf("Image no transform can be fetched...\n");
		GeoTransform = FALSE;
	}

	//*************************************************************************************************

	// Section for tiff input for AATSR
	if ( file_tiff != NULL ){
		if ( ( hSrcTiff = GDALOpen( file_tiff, GA_ReadOnly )) != NULL ){	
			// Very very strict test controll!!
	
			if (	( !strcmp( GDALGetDriverShortName(GDALGetDatasetDriver( hSrcTiff )), "GTiff"  ) )	&&
				( GDALGetRasterCount( hSrcTiff ) == 2 )							&&
				( pxSizeX == GDALGetRasterXSize(hSrcTiff) )						&&
				( pxSizeY == GDALGetRasterYSize(hSrcTiff) )						&&
				( GDALGetRasterDataType( GDALGetRasterBand( hSrcTiff, 1 )) == GDT_Float32 )		&&
				( GDALGetRasterDataType( GDALGetRasterBand( hSrcTiff, 2 )) == GDT_Float32 )		){
	
				printf("Supplied GeoTIFF image for coordinates %s ...\n", file_tiff );

		        	nGCPCount = GDALGetGCPCount(hSrcTiff);

        			if ( nGCPCount > 0 ){
                			pasGCPList 		= ( GDAL_GCP *)GDALGetGCPs(hSrcTiff);
			                pszGCPProjection	= GDALGetGCPProjection(hSrcTiff);
					y 			= ((int)pasGCPList[0].dfGCPLine);
					tie_for_line 		= 0;

					for(i = 0; i < nGCPCount ; i++){
						if ( y != ((int)pasGCPList[i].dfGCPLine) ) { tie_for_line = i; break; }
					}
					if (tie_for_line == 23 ) aatsr_mode = TRUE;

					
				}
				
				if (aatsr_mode == TRUE ){
					printf("GeoTiff coordinates from AATSR image...\n");
					if ( ( tie_point_lon	= (double **)	malloc(sizeof(double *)	* nGCPCount/tie_for_line) ) == NULL ){ printf ("Malloc error tie_point_lon\n"); return 4; }	
					if ( ( tie_point_lat	= (double **)	malloc(sizeof(double *)	* nGCPCount/tie_for_line) ) == NULL ){ printf ("Malloc error tie_point_lat\n"); return 4; }	
					if ( ( tie_point_y	= (int *)	malloc(sizeof(int) 	* nGCPCount/tie_for_line) ) == NULL ){ printf ("Malloc error tie_point_y\n");   return 4; }	

					if ( ( coordMatrixLon	= (double *)	malloc(sizeof(double)	* ((pxSizeX+1) * (pxSizeY+1)) ) ) == NULL ){ printf ("Malloc error coordMatrixLon\n"); return 4; }	
					if ( ( coordMatrixLat	= (double *)	malloc(sizeof(double)	* ((pxSizeX+1) * (pxSizeY+1)) ) ) == NULL ){ printf ("Malloc error coordMatrixLat\n"); return 4; }	

					z = (nGCPCount/tie_for_line);
					for(i = 0 , j = 0, k = 0; i < nGCPCount ; i++){
				                x = ((int)pasGCPList[i].dfGCPPixel);
						y = ((int)pasGCPList[i].dfGCPLine);
						if ( j == 0 ){
							if ( ( tie_point_lon[k] = (double *)malloc(sizeof(double) * tie_for_line) ) == NULL ){ printf ("Malloc error tie_point_lon[%d]\n",k); return 4; }
							if ( ( tie_point_lat[k] = (double *)malloc(sizeof(double) * tie_for_line) ) == NULL ){ printf ("Malloc error tie_point_lat[%d]\n",k); return 4; }
						}
						tie_point_lon[k][j] 	= (double)pasGCPList[i].dfGCPX;
						tie_point_lat[k][j] 	= (double)pasGCPList[i].dfGCPY;


						tie_point_y[k]		= (int)y;
	
						if ( x >= ( pxSizeX -1 )){ j = 0; k++; }
						else j++;
	
					}
					tie_dist_line = ((int)pasGCPList[1].dfGCPPixel) - ((int)pasGCPList[0].dfGCPPixel);

					
					for( i = -1, y = 0 ; i < pxSizeY ; i++){

						if ( i > tie_point_y[y+1]) y++; 
						if ( y >=  (z-1) ) y = z - 2;
		
						point_y = (double)(i - tie_point_y[y] )  / (double)(  tie_point_y[y+1] - tie_point_y[y]  );

						decode_tiepoint( tie_point_lon[y], tie_point_lon[y+1], tie_dist_line, tie_for_line, 1, 0, 
									((double)pasGCPList[0].dfGCPPixel), point_y, pxSizeX+1, 1, coordMatrixLon, (i+1)*(pxSizeX+1) );
						decode_tiepoint( tie_point_lat[y], tie_point_lat[y+1], tie_dist_line, tie_for_line, 0, 0, 
									((double)pasGCPList[0].dfGCPPixel), point_y, pxSizeX+1, 1, coordMatrixLat, (i+1)*(pxSizeX+1) );

					}


			        }


	 			if ( ( tiff_lat = (float *)malloc(sizeof(float) * pxSizeX * pxSizeY) ) == NULL ){
					printf ("Malloc error tiff_lat\n");
					return 4;
				}
				if ( ( tiff_lon = (float *)malloc(sizeof(float) * pxSizeX * pxSizeY) ) == NULL ){
					printf ("Malloc error tiff_lon\n");
					return 4;
				}

				pasGCPList = ( GDAL_GCP *)malloc(sizeof(GDAL_GCP) * pxSizeX * pxSizeY);
				if ( pasGCPList == NULL ){
					printf("Malloc error pasGCPList (%.2f MByte)\n", (double)(sizeof(GDAL_GCP) * pxSizeX * pxSizeY) / 1024.0 / 1024.0 );
					return 2;
				}
				nGCPCount = pxSizeX * pxSizeY;
	
				hBandSrc = GDALGetRasterBand( hSrcTiff, 1 );
				GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, tiff_lat,  pxSizeX, pxSizeY, GDT_Float32, 0, 0);
	
				hBandSrc = GDALGetRasterBand( hSrcTiff, 2 );
				GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, tiff_lon,  pxSizeX, pxSizeY, GDT_Float32, 0, 0);




				if ( ( aatsr_mode == TRUE ) && ( coordMatrixLat != NULL ) && ( coordMatrixLon != NULL ) ){


					MAXLON = MINLON = coordMatrixLon[0];
					for(i = 0 ; i <  (pxSizeX * pxSizeY)  ; i++){
			                        x = (i % pxSizeX);
	       		 		        y = (i / pxSizeX);
						if ( tiff_lon[i] ==	-9999.0	) tiff_lon[i] = (float)coordMatrixLon[ (int)(x + (y+1) * (pxSizeX+1)) ];
						if ( tiff_lat[i] ==	-9999.0	) tiff_lat[i] = (float)coordMatrixLat[ (int)(x + (y+1) * (pxSizeX+1)) ];
						if ( tiff_lon[i] <	-180.0 	) tiff_lon[i] = (float)coordMatrixLon[ (int)(x + (y+1) * (pxSizeX+1)) ];
						if ( tiff_lon[i] > 	 180.0	) tiff_lon[i] = (float)coordMatrixLon[ (int)(x + (y+1) * (pxSizeX+1)) ];
						if ( tiff_lat[i] <	-90.0 	) tiff_lat[i] = (float)coordMatrixLat[ (int)(x + (y+1) * (pxSizeX+1)) ];
						if ( tiff_lat[i] >	 90.0 	) tiff_lat[i] = (float)coordMatrixLat[ (int)(x + (y+1) * (pxSizeX+1)) ];

						if ( tiff_lon[i] <= -180.0 ) tiff_lon[i] += 360.0;
						if ( tiff_lon[i] >=  180.0 ) tiff_lon[i] -= 360.0;

						if ( tiff_lon[i] > MAXLON ) MAXLON = tiff_lon[i];
						if ( tiff_lon[i] < MINLON ) MINLON = tiff_lon[i];
						
					}


					if ( ( MAXLON - MINLON ) > 180.0 ){
						for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
							if ( ( tiff_lon[i]	 > -180.0  ) && ( tiff_lon[i] 		< 0.0 ) ) tiff_lon[i]		+= 360.0;
							if ( ( tiff_lon[i]	 > -180.0  ) && ( tiff_lon[i] 		< 0.0 ) ) tiff_lon[i]		+= 360.0;
							if ( ( coordMatrixLon[i] > -180.0  ) && ( coordMatrixLon[i] 	< 0.0 ) ) coordMatrixLon[i]	+= 360.0;
						}
						for(i = (pxSizeX * pxSizeY) ; i < ((pxSizeX+1) * (pxSizeY+1)) ; i++ ){
							if ( ( coordMatrixLon[i] > -180.0  ) && ( coordMatrixLon[i]     < 0.0 ) ) coordMatrixLon[i]     += 360.0;
						}
					}	
					

					// ************************************************************************************************ //
				
			
					if ( ( xpoly = (double *)malloc(sizeof(double) * pxSizeY ) ) == NULL ){
						printf ("Malloc error xpoly\n");
						return 4;
					}
					if ( ( ypoly = (double *)malloc(sizeof(double) * pxSizeY ) ) == NULL ){
						printf ("Malloc error ypoly\n");
						return 4;
					}


					
					for (j = 0; j <  pxSizeY; j++){
						i = 256 + (j * (pxSizeX+1));
						xpoly[j] = (double)coordMatrixLon[i];
						ypoly[j] = (double)coordMatrixLat[i];
					}
				
					// ************************************************************************************************ //
	

					if ( nGCPCount < 10000 ){ 
						for(i = 0 ; i <  (pxSizeX * pxSizeY)  ; i++){
				                        x = (i % pxSizeX);
		       		 		        y = (i / pxSizeX);
	
	
							// Upper left
							x_i = x;	y_i = y-1;
							if ( y_i == -1 ){ // First line
								j 		= x_i;
								lon_avg_1 	= coordMatrixLon[j];
								lat_avg_1 	= coordMatrixLat[j];
							}else{
								j 		= x_i + (pxSizeX  * y_i);
								lon_avg_1	= tiff_lon[j];
								lat_avg_1	= tiff_lat[j];
							}
						
							// Lower right
							x_i = x+1;	y_i = y;
							if ( x_i == pxSizeX ){ // Last column
								j 		 = x_i + ( (pxSizeX+1) * (y_i+1));
								lon_avg_1	+= coordMatrixLon[j];
								lat_avg_1	+= coordMatrixLat[j];
							}else{
								j 		 = x_i + (pxSizeX  * y_i);
								lon_avg_1	+= tiff_lon[j];
								lat_avg_1	+= tiff_lat[j];
							}
							lon_avg_1 = lon_avg_1 / 2.0;
							lat_avg_1 = lat_avg_1 / 2.0;
	
							
							// Lower left
							x_i = x;        y_i = y;
							j               = x_i + (pxSizeX  * y_i);
							lon_avg_2       = tiff_lon[j];
							lat_avg_2       = tiff_lat[j];
							
	
	
							// Upper right
							x_i = x+1;	y_i = y-1;
							if ( x_i == pxSizeX ){ // Last column
								if ( y_i == -1 ){ // First line
									j                = x_i;
									lon_avg_2       += coordMatrixLon[j];
									lat_avg_2       += coordMatrixLat[j];
								}else{
									j                = x_i + ( (pxSizeX+1) * (y_i+1));
									lon_avg_2       += coordMatrixLon[j];
									lat_avg_2       += coordMatrixLat[j];
								}
							}else{
								if ( y_i == -1 ){ // First line
									j                = x_i;
									lon_avg_2       += coordMatrixLon[j];
									lat_avg_2       += coordMatrixLat[j];
								}else{
	
									j 		 = x_i + (pxSizeX  * y_i);
									lon_avg_2	+= tiff_lon[j];
									lat_avg_2	+= tiff_lat[j];
		
								}
							}
	
							lon_avg_2 = lon_avg_2 / 2.0;
							lat_avg_2 = lat_avg_2 / 2.0;
	
							coordMatrix[0][i] = ( lat_avg_1 + lat_avg_2 ) / 2.0;
							coordMatrix[1][i] = ( lon_avg_1 + lon_avg_2 ) / 2.0;
																
						}

						for(i = 0 ; i <  (pxSizeX * pxSizeY)  ; i++){
	
							tiff_lon[i] = (float)coordMatrix[1][i];
							tiff_lat[i] = (float)coordMatrix[0][i];
							if ( tiff_lon[i] >   180.0 ) tiff_lon[i] -= 360.0;
	
							coordMatrix[0][i] = 0.0;
							coordMatrix[1][i] = 0.0;
						}

					}else{
						for(i = 0 ; i <  (pxSizeX * pxSizeY)  ; i++){
							if ( tiff_lon[i] >   180.0 ) tiff_lon[i] -= 360.0;
							coordMatrix[0][i] = 0.0;
							coordMatrix[1][i] = 0.0;
						}
					}
	
				}


		

				for(i = 0 ; i <  (pxSizeX * pxSizeY)  ; i++){
					lon_gcp = (double)tiff_lon[i];							
					lat_gcp = (double)tiff_lat[i];
		                        x_gcp = (i % pxSizeX);
	        		        y_gcp = (i / pxSizeX);


					sprintf(str,"%d", i);
					pasGCPList[i].pszId = (char *)malloc(sizeof(char) * strlen(str));
					strcpy(pasGCPList[i].pszId, str);
		
					sprintf(str," ");
					pasGCPList[i].pszInfo = (char *)malloc(sizeof(char) * strlen(str));
					strcpy(pasGCPList[i].pszInfo, str);

					pasGCPList[i].dfGCPPixel    = (double)x_gcp;
					pasGCPList[i].dfGCPLine     = (double)y_gcp;

					pasGCPList[i].dfGCPX        = (double)lon_gcp;
					pasGCPList[i].dfGCPY        = (double)lat_gcp;
					pasGCPList[i].dfGCPZ        = 0;
				}


				free(tiff_lon);
				free(tiff_lat);
				GDALClose(hSrcTiff);	

				file_pts	= NULL;
			}
		}else{
			file_tiff = NULL;
		}
	}
	


	//*************************************************************************************************

	// Section from PTS file
	if ( file_pts != NULL ){
		printf("I use input PTS file...\n");
		if((fp = fopen(file_pts,"r")) == NULL) {
			printf("Cannot open file %s.\n", file_pts);
			exit(1);
		}
		pos = (fpos_t *)malloc(sizeof(fpos_t));

		 // Search zone number for conversion UTM latlon, input pts file from MOSID calibration	
		while( fgets(line, 255, fp) != NULL ){ 
			if ( line[0] != ';' ){ // Skip non comment line
				count++ ;
			}else{
				if (strstr(line, "; Zone Number:")){ 
					for( i = 0; i < strlen(line); i++){
						if(line[i] == ':'){
							zone = atoi( &(line[i+2]) );
							if ( line[strlen(line)-2] == 'S' ) NSzone = S_ZONE;
							
						}	
					}
				}
				fgetpos(fp, pos);
			}
		}

		// Zone number found, so .pts file comes from modis calibrator
		if ( zone != NO_ZONE ) {	
			printf("Zone: %d\n", zone);
			// Create a object for conveter from UTM to latlon
			hSourceSRS  = OSRNewSpatialReference(NULL);
			if ( NSzone == S_ZONE )	sprintf(tmp,"+proj=utm +datum=WGS84 +zone=%d  +south	+units=m",zone);
			else			sprintf(tmp,"+proj=utm +datum=WGS84 +zone=%d            +units=m",zone);
			OSRSetFromUserInput( hSourceSRS, tmp );
			hTargetSRS = OSRNewSpatialReference(NULL);

			sprintf(tmp,"+proj=latlong +datum=WGS84");
			OSRSetFromUserInput( hTargetSRS, tmp );

			hCT = OCTNewCoordinateTransformation( hSourceSRS, hTargetSRS ); 
			if( hCT == NULL ){
			        printf("Problem with Coordinates converter\n");
			        return 3;
			}
	
		}else{
			printf("Input PTS file with lat/long format...\n");
			pos = NULL;
			hCT = NULL;
		}

		printf("Found %d GCPs in the PTS file...\n",count);  

		if ( pos != NULL )	fsetpos(fp, pos);
		else			rewind(fp);

		pasGCPList = ( GDAL_GCP *)malloc(sizeof(GDAL_GCP) * count);
		if ( pasGCPList == NULL ){
			printf("Malloc error pasGCPList\n");
			return 2;
		}
	
		nGCPCount = 0;
		while( fscanf(fp, "%lf %lf %lf %lf", &lon_gcp, &lat_gcp, &x_gcp, &y_gcp)!=EOF){
			
			sprintf(str,"%d", nGCPCount);
			
			pasGCPList[nGCPCount].pszId = (char *)malloc(sizeof(char) * strlen(str));
			strcpy(pasGCPList[nGCPCount].pszId, str);
			
			sprintf(str," ");
			pasGCPList[nGCPCount].pszInfo = (char *)malloc(sizeof(char) * strlen(str));
			strcpy(pasGCPList[nGCPCount].pszInfo, str);
	
			pasGCPList[nGCPCount].dfGCPPixel    = (double)x_gcp;
			pasGCPList[nGCPCount].dfGCPLine     = (double)y_gcp;
			if (hCT != NULL){
				GeoX = (double)lon_gcp;
				GeoY = (double)lat_gcp;
				OCTTransform(hCT, 1, &GeoX, &GeoY, NULL);
				lon_gcp = (float)GeoX;
				lat_gcp = (float)GeoY;
			}

			pasGCPList[nGCPCount].dfGCPX        = (double)lon_gcp;
			pasGCPList[nGCPCount].dfGCPY        = (double)lat_gcp;
			pasGCPList[nGCPCount].dfGCPZ        = 0;
			nGCPCount++;
			
		}
		fclose(fp); 


	} else if (file_tiff == NULL) {
		// Try to find GCPs into image
	        nGCPCount = GDALGetGCPCount(hSrcDS);
		if ( nGCPCount != 0 ){	
	                pasGCPList = (GDAL_GCP *)GDALGetGCPs(hSrcDS);
	                pszGCPProjection = GDALGetGCPProjection(hSrcDS);
		}

	}



	//*************************************************************************************************

	// If pts file comes from sensors that is not modis
	if ( ( zone == NO_ZONE ) && ( nGCPCount != 0 ) && ( nGCPCount != (pxSizeX * pxSizeY) )) {
		printf("Detected PTS from ");
		y = ((int)pasGCPList[0].dfGCPLine);
		tie_for_line = 0;
		for(i = 0; i < nGCPCount ; i++){
			if ( y != ((int)pasGCPList[i].dfGCPLine) ) { tie_for_line = i; break; }
		}
		switch(tie_for_line){
			case 23: 
				printf("AATSR image...\n");
				aatsr_mode = TRUE;
				break;
			case 71:
				printf("MERIS image...\n");
				break;
			case 0:
				printf("detection ERROR\n");	
				return 10;
			default:
				printf("Unknown image...\n");
				break;
						
		}


		z = (nGCPCount/tie_for_line);
		printf("Dim. of GCPs: %dx%d\n", tie_for_line, z );

		if ( ( tie_point_lon = (double **)malloc(	sizeof(double *) 	* z ) ) == NULL ){
			printf ("Malloc error tie_point_lon\n");
			return 4;
		}	
		if ( ( tie_point_lat = (double **)malloc(	sizeof(double *) 	* z ) ) == NULL ){
			printf ("Malloc error tie_point_lat\n");
			return 4;
		}	
		if ( ( tie_point_y = (int *)malloc(		sizeof(int)		* z ) ) == NULL ){
			printf ("Malloc error tie_point_y\n");
			return 4;
		}	

		
		printf("Creating matrix of tie points for interpolation...\n");
		for(i = 0 , j = 0, k = 0; i < nGCPCount ; i++, k = i / tie_for_line, j = i % tie_for_line){

	                x = ((int)pasGCPList[i].dfGCPPixel);
			y = ((int)pasGCPList[i].dfGCPLine);

			if ( j == 0 ){
				if ( ( tie_point_lon[k] = (double *)malloc(sizeof(double) * tie_for_line) ) == NULL ){
					printf ("Malloc error tie_point_lon[%d]\n", k);
					return 4;
				}
				if ( ( tie_point_lat[k] = (double *)malloc(sizeof(double) * tie_for_line) ) == NULL ){
					printf ("Malloc error tie_point_lat[%d]\n", k);
					return 4;
				}

			}

			tie_point_lon[k][j] 	= (double)pasGCPList[i].dfGCPX;
			tie_point_lat[k][j] 	= (double)pasGCPList[i].dfGCPY;
			tie_point_y[k]		= (int)y;
			

			/*
			if (x >= ( pxSizeX -1 )){ j = 0; k++; }
			else			j++;
			*/
	
		}

		tie_dist_line = ((int)pasGCPList[1].dfGCPPixel) - ((int)pasGCPList[0].dfGCPPixel);
		printf("Starting interpolation...\n");

		if ( aatsr_mode == TRUE ) { dfGCPPixelOffsetLon = 0.5f; dfGCPPixelOffsetLat = 0.5f; }

		for( i = 0, y = 0 ; i < pxSizeY ; i ++){

			if ( i > tie_point_y[y+1]) y++; 

			if ( y >=  (z-1) ) y = z - 2;
		
			point_y = (double)(i - tie_point_y[y] + dfGCPPixelOffsetLat )  / (double)(  tie_point_y[y+1] - tie_point_y[y]  );

		
			decode_tiepoint( tie_point_lon[y], tie_point_lon[y+1], tie_dist_line, tie_for_line, 1, 0, ((double)pasGCPList[0].dfGCPPixel) - dfGCPPixelOffsetLon, point_y, pxSizeX, 1, coordMatrix[1], i*pxSizeX );
			decode_tiepoint( tie_point_lat[y], tie_point_lat[y+1], tie_dist_line, tie_for_line, 0, 0, ((double)pasGCPList[0].dfGCPPixel), point_y, pxSizeX, 1, coordMatrix[0], i*pxSizeX );

		}


		if (( xpoly == NULL ) && ( ypoly == NULL ) && ( aatsr_mode == TRUE ) ){
			if ( ( xpoly = (double *)malloc(sizeof(double) * pxSizeY ) ) == NULL ){
				printf ("Malloc error xpoly\n");
				return 4;
			}
			if ( ( ypoly = (double *)malloc(sizeof(double) * pxSizeY ) ) == NULL ){
				printf ("Malloc error ypoly\n");
				return 4;
			}



			for (j = 0; j <  pxSizeY; j++){
				i = 256 + (j * pxSizeX);
				xpoly[j] = (double)coordMatrix[1][i];
				ypoly[j] = (double)coordMatrix[0][i];
			}
		}

		printf("Re-make CGPs from tie points...\n");
		pasGCPList = ( GDAL_GCP *)malloc(sizeof(GDAL_GCP) * pxSizeX * pxSizeY);
		if ( pasGCPList == NULL ){
			printf("Malloc error pasGCPList\n");
			return 2;
		}
		for (i = 0, nGCPCount = 0; i < (pxSizeX * pxSizeY); i++, nGCPCount++){
			x_gcp = (i % pxSizeX);
	                y_gcp = (i / pxSizeX);

			sprintf(str,"%d", nGCPCount);
		
			pasGCPList[nGCPCount].pszId = (char *)malloc(sizeof(char) * strlen(str));
			strcpy(pasGCPList[nGCPCount].pszId, str);
			
			sprintf(str," ");
			pasGCPList[nGCPCount].pszInfo = (char *)malloc(sizeof(char) * strlen(str));
			strcpy(pasGCPList[nGCPCount].pszInfo, str);
	
			pasGCPList[nGCPCount].dfGCPPixel    = (double)x_gcp;
			pasGCPList[nGCPCount].dfGCPLine     = (double)y_gcp;

			pasGCPList[nGCPCount].dfGCPX        = (double)coordMatrix[1][i];
			pasGCPList[nGCPCount].dfGCPY        = (double)coordMatrix[0][i];
			pasGCPList[nGCPCount].dfGCPZ        = 0;

		}

	}

	//*************************************************************************************************



	if  ( nGCPCount != 0 ){
		printf("Image with %d GCPs...\n", nGCPCount);
		if( GRID_MODE == TRUE ){
			GDALGCPsToGeoTransform( nGCPCount, pasGCPList, padfGeoTransform, TRUE);
			if ( GDALInvGeoTransform(padfGeoTransform,gridGeoTransform) == FALSE ){
				printf("Problem with inversion of matrix\n");
				return 3;				
			}
		}

	} else {
		printf("Image without GCPs...\n"); 
	
		if ( GeoTransform != FALSE ){

			printf("Try to create GCPs from GeoTransform matrix...\n");
			hSourceSRS = OSRNewSpatialReference(NULL);  
			if( OSRImportFromWkt( hSourceSRS, &pszTargetSRS ) != CE_None )	pszTargetSRS = NULL;


			zone = OSRGetUTMZone(hSourceSRS, &pbNorth);	
			hTargetSRS = OSRNewSpatialReference(NULL);
			sprintf(tmp,"+proj=latlong +datum=WGS84");
			OSRSetFromUserInput( hTargetSRS, tmp );

			// Close check to indetify if input is already remapper granule
			if ( 	( padfGeoTransform[1] == COORD_STEP )			&&
				( padfGeoTransform[2] == 0.0 )				&&
				( padfGeoTransform[4] == 0.0 )				&&
				( padfGeoTransform[5] == (COORD_STEP * -1.0) )		){

				MUST_ONLY_CUT = TRUE;	
			}


			if (( OUTPUT_IN_METERS == FALSE ) && (pszTargetSRS != NULL) ){
				hCT = OCTNewCoordinateTransformation( hSourceSRS, hTargetSRS ); 
				if( hCT == NULL ){
				        printf("Problem with Coordinates converter\n");
				        return 3;
				}
			}
			if( GRID_MODE == TRUE ){
				if ( GDALInvGeoTransform(padfGeoTransform,gridGeoTransform) == FALSE ){
					printf("Problem with inversion of matrix\n");
					return 3;				
				}
			}


			if (( MUST_ONLY_CUT == TRUE ) && ( GRID_MODE == TRUE ) && ( date_start != NULL ) && ( date_end != NULL ) ){

			        papszMetadata   = GDALGetMetadata(hSrcDS, NULL);
			        nCount          = CSLCount(papszMetadata);
	 			if ( ( track_line_index = (int *)malloc(sizeof(int) * nCount) ) == NULL ){
					printf ("Malloc error track_line_index\n");
					return 4;
				}
	

				printf("Testing Meta-Tag for Track information...\n");
			        for( i = 0, j = 0, track_line_num = 0; i < nCount; i++ ){
					track_line_index[i] = -1;
					sprintf(tmp, "T%d", j);
			                pszValue = (const char *)CPLParseNameValue( papszMetadata[i], &pszKey );
					if (!strcmp(tmp, pszKey)){ track_line_index[i] = atoi(&pszKey[1]); j+=3; track_line_num++; }
					
				}
				if ( track_line_num != 0 ){
					TRACK_LINE = TRUE;	
					printf("Found %d tags...\n", track_line_num );

		 			if ( ( track_line = (int *)malloc(sizeof(int) * track_line_num) ) == NULL ){
						printf ("Malloc error track_line\n");
						return(4);
					}
			
		 			if ( ( track_line_x = (int *)malloc(sizeof(int) * track_line_num) ) == NULL ){
						printf ("Malloc error track_line_x\n");
						return(4);
					}
		 			if ( ( track_line_y = (int *)malloc(sizeof(int) * track_line_num) ) == NULL ){
						printf ("Malloc error track_line_y\n");
						return(4);
					}
	
					for( i = 0, j= 0; i < nCount; i++ ){
						if ( track_line_index[i] == -1 ) continue;

						sprintf(tmp, "T%d", track_line_index[i]);
						pszValue = (const char *)CPLParseNameValue( papszMetadata[i], &pszKey );
						sscanf(pszValue,"%d,%d", &track_line_x[j], &track_line_y[j]);
						track_line[j] =  track_line_index[i];
						j++;
					}
					time4line = getTimeForLine(date_start, date_end, track_line[track_line_num-1]);
					printf("Reinitialize Time of one line with Meta-Tag: %f\n", time4line);
				}


				free(coordMatrix[0]);			
				free(coordMatrix[1]);
				free(coord_info);

				coordMatrix[0]	= NULL;
				coordMatrix[1]	= NULL;
				coord_info	= NULL;

			}else{
	                        for(i = 0 ; i < (pxSizeX * pxSizeY ) ; i++ ){
	                                x = (i % pxSizeX);
        	                        y = (i / pxSizeX);
	
	                                GDALApplyGeoTransform(padfGeoTransform, x, y, &lon, &lat );
        	                        if (hCT != NULL) OCTTransform(hCT, 1, &lon, &lat, NULL);
        	                        coordMatrix[0][i] = lat;
        	                        coordMatrix[1][i] = lon;
        	                        coord_info[i]     = YES_VALUE;
        	                }


			}
			pasGCPList = NULL;
		}else{
			printf("Image without georeference... I can't do a miracle.\n");
			return(4); 

		}
	}


	//*************************************************************************************************


	// Maps the real PCs on input image
	if ( pasGCPList != NULL ){
		printf("Testing GCPs...\n");
		// Initialize coordinates matrix
		for(i = 0 ; i < (pxSizeX * pxSizeY ) ; i++ ){
			coordMatrix[0][i] 	= NO_VALUE;
			coordMatrix[1][i] 	= NO_VALUE;
			coord_info[i]		= NO_VALUE;
		}
		for(i = 0 ; i < nGCPCount ; i++){
			x = ((int)pasGCPList[i].dfGCPPixel);
			y = ((int)pasGCPList[i].dfGCPLine);

			j = x + ( y * pxSizeX ) ;


			// Latitude
			coordMatrix[0][j]	= pasGCPList[i].dfGCPY;
			// Longitude
			coordMatrix[1][j]	= pasGCPList[i].dfGCPX;
			//
			coord_info[j]		= YES_VALUE;


		}
		free(pasGCPList);
	}

	// Calculation of distance between GPCs
	x_win = y_win = 0;
	if ( ( coordMatrix[0] != NULL ) && ( coordMatrix[1] != NULL ) ){
		for(i = 0 ; i < (pxSizeX * pxSizeY ) ; i++ ){
			if (coord_info[i] != NO_VALUE){
				x = (i % pxSizeX);
		                y = (i / pxSizeX);
				for(i++; i < ( (x+1) * pxSizeX ); i++ ){
					if (coord_info[i] != NO_VALUE){
						x_win = (i % pxSizeX) - x - 1;
						x = (i % pxSizeX);
        	        			y = (i / pxSizeX);
						break;
					}				
				}
				for( i = ( i + pxSizeX - x_win - 1) ; i < ( pxSizeX * pxSizeY ); i+= pxSizeX ){
					if (coord_info[i] != NO_VALUE){
						y_win = (i / pxSizeX) - y - 1;
						x = (i % pxSizeX);
        	        			y = (i / pxSizeX);
						break;
					}					
				}
				break;
			}
		}
	}

	//*************************************************************************************************

	if (( x_win == 0 ) && (y_win == 0 )){ // If window size of GPCs is 0x0 the grid is filled 
		printf("Grid filled in every cell...\n");
	}else{
		// Otherwise I must interpolate to filling every pixel (MODIS)
		printf("GCPs grid size: %dx%d\n", x_win, y_win);
		printf("Filling the empty cells...\n");

		if ( ( weigh  = (double *)malloc(sizeof(double) * (2*x_win+1) * (2*y_win+1) ) ) == NULL ){
			printf ("Malloc error weigh\n");
			return(4);
		}
	

		if ( ( dist = (double *)malloc(sizeof(double) *	(2*x_win+1) * (2*y_win+1) ) ) == NULL ){
			printf ("Malloc error dist\n");
			return(4);
		}

		if ( ( near_list = (int *)malloc(sizeof(int) *	(2*x_win+1) * (2*y_win+1) ) ) == NULL ){
			printf ("Malloc error near_list\n");
			return(4);
		}

		
		for(i = 0 ; i < (pxSizeX * pxSizeY ) ; i++ ){

			if (coord_info[i] == NO_VALUE){

	                        // Calculate coordinates
	                        x = (i % pxSizeX);
	                        y = (i / pxSizeX);

				// Up left corner of win
                                x_win_UL = x - x_win;
                                if (x_win_UL < 0 ) x_win_UL = 0;
                                y_win_UL = y - y_win;
                                if (y_win_UL < 0 ) y_win_UL = 0;

				// Low Right corner of win
                                x_win_LR = x + x_win;
                                if (x_win_LR >= pxSizeX ) x_win_LR = (pxSizeX-1);
                                y_win_LR = y + y_win;
                                if (y_win_LR >= pxSizeY ) y_win_LR = (pxSizeY-1);

				num_near = 0;
				dist_tot = 0;
                                for ( j = y_win_UL ; j < y_win_LR+1  ; j++){
                                        for ( k = x_win_UL ; k < x_win_LR+1  ; k++){
                                                i_win =  k + ( j * pxSizeX );
						if (coord_info[i_win] != NO_VALUE){
							dist[num_near] 		= sqrt( (float)((k - x) * (k - x) + (j - y)*(j - y)) );
							dist_tot 		+= dist[num_near];
							near_list[num_near]	= i_win;
							num_near++;

						} 
                                        }
                                }
			
				// Initialize coordinates
				coordMatrix[0][i] = coordMatrix[1][i] = 0;
				for(j = 0 ; j < num_near ; j++){
					if (num_near == 1 ) weigh[j] = 1;
					else weigh[j] =  ( 1 - ( dist[j] / dist_tot) ) / (num_near - 1 );
					// Latitude
					coordMatrix[0][i] += ( weigh[j] * coordMatrix[0][ near_list[j] ] );
					// Longitude
					coordMatrix[1][i] += ( weigh[j] * coordMatrix[1][ near_list[j] ] );
				}
			}
		}
	}
	

	//*************************************************************************************************

	// Search min and max longitude to indetify cross date line

	if ( OUTPUT_IN_METERS == FALSE ){

		if ( ( coordMatrix[0] != NULL ) && ( coordMatrix[1] != NULL ) ){

			MINLON = MAXLON = coordMatrix[1][0];
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				if ( coordMatrix[1][i] < -180.0 	) coordMatrix[1][i]	+= 360.0;
				if ( coordMatrix[1][i] > 180.0		) coordMatrix[1][i]	-= 360.0;
				if ( coordMatrix[1][i] > MAXLON 	) MAXLON		= coordMatrix[1][i];
				if ( coordMatrix[1][i] < MINLON 	) MINLON		= coordMatrix[1][i];

			}

			if ( ( MAXLON - MINLON ) > 360.0f ) {
				printf("Logitude cross The International Date Line...\n");
				for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
					if ( ( coordMatrix[1][i] >= -180.0  ) && ( coordMatrix[1][i] < 0.0  ) ) coordMatrix[1][i] += 360.0;
				}
				CROSS_DATE_LINE = TRUE;
			}
		}else{
			GDALApplyGeoTransform(padfGeoTransform, 0, 0, &lon, &lat);
			MINLON = MAXLON = lon;
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				GDALApplyGeoTransform(padfGeoTransform, (double)(i % pxSizeX), (double)(i / pxSizeX) , &lon, &lat);
				if ( lon > MAXLON ) MAXLON = lon;
				if ( lon < MINLON ) MINLON = lon;
			}

			if ( MAXLON > 180.0f ) {
				printf("Logitude cross The International Date Line...\n");
				CROSS_DATE_LINE = TRUE;
			}
		}
	}


	//*************************************************************************************************
	// If the flag is set search bouding box to get AOI where I must remap

	if (	( FIX_lat	== TOBBOX ) 		&& ( FIX_lon	== TOBBOX )	&&
		( LR_FIX_lat	== TOBBOX ) 		&& ( LR_FIX_lon	== TOBBOX )	&&
		( INPUT_TYPE	== INPUT_LATLON )	&& ( BBOX 	== TRUE	)	){

		printf("Searching Bounding Box...\n");

		FIX_lat = LR_FIX_lat = coordMatrix[0][0];
		FIX_lon = LR_FIX_lon = coordMatrix[1][0]; 

		for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
			if ( coordMatrix[0][i] > FIX_lat	) FIX_lat	= coordMatrix[0][i];
			if ( coordMatrix[0][i] < LR_FIX_lat	) LR_FIX_lat	= coordMatrix[0][i];

			if ( coordMatrix[1][i] < FIX_lon	) FIX_lon	= coordMatrix[1][i];
			if ( coordMatrix[1][i] > LR_FIX_lon	) LR_FIX_lon	= coordMatrix[1][i];
		}
	
		if ( BBOX_GRID == TRUE ){
			printf("Closing Bounding Box in Earth Fixed Grid...\n");
	                FIX_lat		= closeEarthFixed(FIX_lat,	1.0 / ( COORD_STEP * 64.0 ), 1);
	                FIX_lon		= closeEarthFixed(FIX_lon,	1.0 / ( COORD_STEP * 64.0 ), 0); 

	                LR_FIX_lat	= closeEarthFixed(LR_FIX_lat,	1.0 / ( COORD_STEP * 64.0 ), 0);
	                LR_FIX_lon	= closeEarthFixed(LR_FIX_lon,	1.0 / ( COORD_STEP * 64.0 ), 1);
		}

		if ( LR_FIX_lon > 180.0f ){ 
			printf("      Upper left  Lat: %f / Lon: %f\n", FIX_lat, 	FIX_lon);
			printf("      Lower right Lat: %f / Lon: %f\n", LR_FIX_lat, 	LR_FIX_lon - 360.0f );
		}else{
			printf("      Upper left  Lat: %f / Lon: %f\n", FIX_lat, 	FIX_lon);
			printf("      Lower right Lat: %f / Lon: %f\n", LR_FIX_lat, 	LR_FIX_lon);
		}

	}
		
	
	//*************************************************************************************************


	if ( GRID_MODE == FALSE ) {
		if ( ( BBOX == FALSE ) && ( OUTPUT_IN_METERS == FALSE ) ){

			MAXLON = ( LR_FIX_lon > FIX_lon ) ? LR_FIX_lon : FIX_lon;
			MINLON = ( LR_FIX_lon < FIX_lon ) ? LR_FIX_lon : FIX_lon;

			if ( ( MAXLON - MINLON ) > 360.0f ){
				printf("Input coordinates cross International Date Line...\n");
				LR_FIX_lon = LR_FIX_lon + 360.0f;
			}
		}

	        if ( INPUT_TYPE == INPUT_LATLON ){
			printf("Search end pixel coords..\n");
			WIN_SIZE_X = (LR_FIX_lon - FIX_lon	) / COORD_STEP;
			WIN_SIZE_Y = (FIX_lat 	 - LR_FIX_lat	) / COORD_STEP;

	
	        }


		if ( OUTPUT_UTM == FALSE ){
			if (( WIN_SIZE_X <= 0 ) || ( WIN_SIZE_Y <= 0 )){
				printf("Input coordinates for Lower Right corner are invalid!\n");
				return 1;
	
			}	
		}

		UL_array = UP_cursor = (COORD *)malloc(sizeof(COORD));
		if ( UP_cursor == NULL ){
		printf ("Malloc error UP_cursor\n");
			return 4;
		}

		UP_cursor->lat 	= FIX_lat;
		UP_cursor->lon 	= FIX_lon;
		UP_cursor->next	= NULL;


	}

	//*************************************************************************************************

	if(( GRID_MODE == TRUE ) && ( OUTPUT_UTM == FALSE )) { // MUAHAHAAHHAHAH!!!
		printf("Earth Fixed GRID mode...\n");
		printf("Creating GRID...\n");


		// If it is in input, create a dinamic list structure of file content
		if ( good_tile != NULL ){
			printf("Create list of good tiles from %s file...\n", good_tile);
			GT_array = GT_head = GT_cursor = (COORD *)malloc(sizeof(COORD));
			if ( GT_cursor == NULL ){
				printf ("Malloc error GT_cursor\n");
				return(4);
			}
			if((fp = fopen(good_tile,"r")) == NULL) {
				printf("Cannot open file %s.\n", file_pts);
				return(1);
			}
			i = 0;

			while( fscanf(fp, "%lf %lf", &fi, &fj) != EOF  ){
				GT_cursor->lat 	= fi;
				GT_cursor->lon 	= fj;

		

				if ( ( CROSS_DATE_LINE == TRUE ) && ( GT_cursor->lon < 0.0 ) ) GT_cursor->lon += 360.0f;

				if (GT_head->lat != GT_cursor->lat){
					GT_cursor->right->left	= NULL;
					GT_head->next 		= GT_cursor;
					GT_head			= GT_head->next;
				}


				i++;

				GT_cursor->left = (COORD *)malloc(sizeof(COORD));
				if ( GT_cursor->left == NULL ){
					printf ("Malloc error GT_cursor->left\n");
					return(4);
				}
				GT_cursor->left->right	= GT_cursor;
				GT_cursor		= GT_cursor->left;
				GT_cursor->left		= NULL;
				GT_cursor->next		= NULL;		
			}

			fclose(fp);
		}	

		// Search bouding box of image to calculate which tiles I must get
		if ( ( coordMatrix[0] != NULL ) && ( coordMatrix[1] != NULL ) ){
			MINLAT = MAXLAT = coordMatrix[0][0];
			MINLON = MAXLON = coordMatrix[1][0]; 
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				MINLAT	= ( coordMatrix[0][i] < MINLAT ) ? coordMatrix[0][i] : MINLAT;
				MAXLAT	= ( coordMatrix[0][i] > MAXLAT ) ? coordMatrix[0][i] : MAXLAT;
				MINLON	= ( coordMatrix[1][i] < MINLON ) ? coordMatrix[1][i] : MINLON;
				MAXLON	= ( coordMatrix[1][i] > MAXLON ) ? coordMatrix[1][i] : MAXLON;

			}
		}else{
                        GDALApplyGeoTransform(padfGeoTransform, 0, 0, &lon, &lat);
			MINLAT = MAXLAT = lat;
                        MINLON = MAXLON = lon;
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				GDALApplyGeoTransform(padfGeoTransform, (double)(i % pxSizeX), (double)(i / pxSizeX) , &lon, &lat);
				MINLAT	= ( lat < MINLAT ) ? lat : MINLAT;
				MAXLAT	= ( lat > MAXLAT ) ? lat : MAXLAT;
				MINLON	= ( lon < MINLON ) ? lon : MINLON;
				MAXLON	= ( lon > MAXLON ) ? lon : MAXLON;

			}
		}

		
		if ( MINLON >= 180.0  	) MINLON -= 360.0;
		if ( MAXLON >= 180.0  	) MAXLON -= 360.0;
		if ( MINLON < -180.0 	) MINLON += 360.0;
		if ( MAXLON < -180.0 	) MAXLON += 360.0;

		if ( MINLAT >= 90.0  	) MINLON -= 180.0;
		if ( MAXLAT >= 90.0	) MAXLON -= 180.0;
		if ( MINLAT < -90.0 	) MINLON += 180.0;
		if ( MAXLAT < -90.0 	) MAXLON += 180.0;
		
		if ( ( MAXLON - MINLON ) > 180.0 ){
			fi 	= MAXLON;
			MAXLON 	= MINLON;
			MINLON	= fi;
		}

		printf("\tMINLAT %f\n",	MINLAT);
                printf("\tMAXLAT %f\n",	MAXLAT);
                printf("\tMINLON %f\n",	MINLON);
	        printf("\tMAXLON %f\n",	MAXLON);

		if ( CROSS_DATE_LINE == TRUE ) MAXLON += 360.0f;

		coord_step_lon	= COORD_STEP * WIN_SIZE_X;
		coord_step_lat	= COORD_STEP * WIN_SIZE_Y;

		name_tile_decimal = decimalCounter(coord_step_lon);
		printf("\tSize of tile in degree: %.*f x %.*f\n", name_tile_decimal, coord_step_lon, name_tile_decimal, coord_step_lat);


		// From real size to earth fixed grid size
		MINLAT = (float)(int)MINLAT + (float)(((int)((MINLAT - (int)MINLAT)/coord_step_lat))  )	* coord_step_lat;
		MAXLAT = (float)(int)MAXLAT + (float)(((int)((MAXLAT - (int)MAXLAT)/coord_step_lat))+1)	* coord_step_lat;

		MINLON = (float)(int)MINLON + (float)(((int)((MINLON - (int)MINLON)/coord_step_lon))  )	* coord_step_lon;
		MAXLON = (float)(int)MAXLON + (float)(((int)((MAXLON - (int)MAXLON)/coord_step_lon))+1)	* coord_step_lon;
		
		printf("\tValue in the GRID:\n");
		printf("\tMINLAT %.*f\n", name_tile_decimal,	MINLAT);
                printf("\tMAXLAT %.*f\n", name_tile_decimal,	MAXLAT);
                printf("\tMINLON %.*f\n", name_tile_decimal,	MINLON);
	        if ( CROSS_DATE_LINE != TRUE )	printf("\tMAXLON %.*f\n", name_tile_decimal,	MAXLON		);
		else				printf("\tMAXLON %.*f\n", name_tile_decimal, 	MAXLON - 360.0f	);

		UL_array = UP_cursor = (COORD *)malloc(sizeof(COORD));
		if ( UP_cursor == NULL ){
			printf ("Malloc error UL_array\n");
			return(4);
		}

		i = 0;
		fi = MAXLAT;

		while ( fi >  (MINLAT-coord_step_lat) ){

			// Search if with lat is good
			if ( good_tile != NULL ){
				z = FALSE;
				for ( GT_head = GT_array; GT_head != NULL ; GT_head = GT_head->next ){
					if (GT_head->lat == fi ){
						z = TRUE; // It's good
						break;
					}
				}
				if (z == FALSE ){ // It isnt good.. go away...
					fi -= coord_step_lat;
					continue;
				}
			}

			z = TRUE; 
			if (( i % 2 ) == 1 ){
				fj = MAXLON;
				while ( fj >= (MINLON-coord_step_lon) ){

					UP_cursor->lat 	= fi;
					UP_cursor->lon 	= fj;
					UP_cursor->next	= NULL;

					// Search tile in good list of tiles
					if ( good_tile != NULL ){
						z = FALSE;
						for ( GT_cursor = GT_head; GT_cursor != NULL ; GT_cursor = GT_cursor->left ){

							if (GT_cursor->lon == UP_cursor->lon ){
								z = TRUE;
								break;
							}
						}
					}
					//---------------------------------------

					fj -= coord_step_lon;

					if (z == FALSE ) continue;
	
					UP_cursor->next = (COORD *)malloc(sizeof(COORD));
					if ( UP_cursor == NULL ){
						printf ("Malloc error UP_cursor->next\n");
						return(4);
					}

					UP_cursor->next->prev = UP_cursor;
					UP_cursor	= UP_cursor->next;
					UP_cursor->lat  = 0.0f;
					UP_cursor->lon  = 0.0f;
					UP_cursor->next = NULL;

				}

			}else{
				fj = MINLON;
				while ( fj <= (MAXLON+coord_step_lon) ){

					UP_cursor->lat 	= fi;
					UP_cursor->lon 	= fj;
					UP_cursor->next	= NULL;

					// Search tile in good list of tiles
					if ( good_tile != NULL ){
						z = FALSE;
						for ( GT_cursor = GT_head; GT_cursor != NULL ; GT_cursor = GT_cursor->left ){

							if (GT_cursor->lon == UP_cursor->lon ){
								z = TRUE;
								break;
							}
						}
					}

					fj += coord_step_lon;	
					if (z == FALSE ) continue;
					UP_cursor->next = (COORD *)malloc(sizeof(COORD));
					if ( UP_cursor->next == NULL ){
						printf ("Malloc error UP_cursor->next\n");
						return(4);
					}

					UP_cursor->next->prev = UP_cursor;
					UP_cursor	= UP_cursor->next;
					UP_cursor->lat  = 0.0f;
					UP_cursor->lon  = 0.0f;
					UP_cursor->next = NULL;

				}
			}
			fi -= coord_step_lat;
			i++;
		}
		// Removed unused last box
		
		if ( UL_array->next != NULL ){
			for ( UP_cursor = UL_array; UP_cursor->next->next != NULL ; UP_cursor = UP_cursor->next );
			UP_cursor->next = NULL;
		}

	}


	//*************************************************************************************************


	k		= 0;
	dist_avg	= 0;
	index_remap	= 0;

	if ( ( MUST_ONLY_CUT == TRUE ) && ( OUTPUT_IN_METERS == FALSE ) && ( GRID_MODE == TRUE ) ){
		printf("Input image uses GeoTransform and has same pixel resolution...\n");
		GDALApplyGeoTransform(gridGeoTransform, (double)UL_array->lon, (double)UL_array->lat, &x_near, &y_near);

		if ( x_near > (double)pxSizeX ) x_near = (double)(pxSizeX-1);
		if ( x_near < 0.0 )             x_near = 0.0;

		if ( y_near > (double)pxSizeY ) y_near = (double)(pxSizeY-1);
		if ( y_near < 0.0)              y_near = 0.0;


		index_remap	= (int)x_near + ( (int)y_near * pxSizeX );
		dist_avg	= COORD_STEP;
		for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ) dist_max[i] = dist_avg;

	}else{
		printf("Search start pixel coords and calculating thresholds ...\n");
		if ( OUTPUT_IN_METERS == FALSE ){

			FIX_dist = distAprox(UL_array->lat, UL_array->lon,  coordMatrix[0][0], coordMatrix[1][0] );
	
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				FIX_new_dist = distAprox(UL_array->lat, UL_array->lon,  coordMatrix[0][i], coordMatrix[1][i] );
				if ( FIX_new_dist < FIX_dist ) {
					FIX_dist = FIX_new_dist;
					index_remap = i; 
				}
	
				x = (i % pxSizeX);
				y = (i / pxSizeX);	
				if ( x > (pxSizeX - 2) ){ dist_max[i] = dist_max[i-1]; continue; }
	
				j = (x + 1) + ( y * pxSizeX );
	
				dist_max[i] = distAprox( coordMatrix[0][j], coordMatrix[1][j], coordMatrix[0][i], coordMatrix[1][i]);
	
				dist_avg += dist_max[i];
				k++;
			}
		}else{
			FIX_dist = sqrt( pow( UL_array->lon - coordMatrix[1][0], 2) + pow( UL_array->lat - coordMatrix[0][0], 2) );
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				FIX_new_dist = sqrt( pow( UL_array->lon - coordMatrix[1][i], 2) + pow( UL_array->lat - coordMatrix[0][i], 2) );
		
				if ( FIX_new_dist < FIX_dist ) {
					FIX_dist = FIX_new_dist;
					index_remap = i; 
				}
	
				x = (i % pxSizeX);
				y = (i / pxSizeX);	
				if ( x > (pxSizeX - 2) ){ dist_max[i] = dist_max[i-1]; continue; }
	
				j = (x + 1) + ( y * pxSizeX );
	
				dist_max[i] = sqrt( pow(  coordMatrix[1][j] - coordMatrix[1][i], 2) + pow( coordMatrix[0][j]  - coordMatrix[0][i], 2) ); 
	
				dist_avg += dist_max[i];
				k++;
			}
		}
		dist_avg = dist_avg / (double)(k);
	}



	//*************************************************************************************************
	
		
	for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ) if ( dist_max[i] < dist_avg )  dist_max[i] = dist_avg * 2;
	
		
	

	if ( OUTPUT_UTM != TRUE ){
		if ( OUTPUT_IN_METERS != TRUE ) printf("ROI size: %dx%d, Pixex size in degree: %.*f, ", WIN_SIZE_X, WIN_SIZE_Y, decimalCounter(COORD_STEP), COORD_STEP);
		else				printf("ROI size: %dx%d, Pixex size in meters: %.*f, ", WIN_SIZE_X, WIN_SIZE_Y, decimalCounter(COORD_STEP), COORD_STEP);
	}

	printf("%dx%d with dist: %f meters\n", index_remap % pxSizeX,  index_remap / pxSizeX, FIX_dist);
	printf("Average pixel dist: %f meters\n", dist_avg);

	if( GRID_MODE == FALSE )	printf("Searching window: %dx%d pixels\n", search_win[0], search_win[1]);
	if( RAW_OUTPUT == TRUE )	printf("Raw output setting...\n");


	//*************************************************************************************************




	//*************************************************************************************************


	if ( OUTPUT_IN_METERS != TRUE )	sprintf(tmp,"+proj=latlong +datum=WGS84");
	else {		
		if ( pbNorth == 1 ) 	sprintf(tmp,"+proj=utm +zone=%d +datum=WGS84 +units=m", 	zone);
		else			sprintf(tmp,"+proj=utm +zone=%d +datum=WGS84 +units=m +south",	zone);
	}

	hTargetSRS = OSRNewSpatialReference(NULL);
	OSRSetFromUserInput( hTargetSRS, tmp );
	OSRExportToWkt( hTargetSRS, &pszTargetSRS);
	//papszOptions = (char **)CSLSetNameValue( papszOptions, "COMPRESS", "LZW" );



	
	// Malloc output
	if ( ( output = (GByte *)malloc(size * WIN_SIZE_X * WIN_SIZE_Y) ) == NULL ){
		printf ("Malloc error output\n");
		return 4;
	}

	if ( STORE_COORDS == TRUE ){
		printf("Output is Remapped matrix... \n");
		if ( ( matrixRemap[0] = (unsigned short int *)malloc(sizeof(unsigned short int) * WIN_SIZE_X * WIN_SIZE_Y) ) == NULL ){
			printf ("Malloc error matrixRemap[0]\n");
			return 4;
		}
		if ( ( matrixRemap[1] = (unsigned short int *)malloc(sizeof(unsigned short int) * WIN_SIZE_X * WIN_SIZE_Y) ) == NULL ){
			printf ("Malloc error matrixRemap[1]\n");
			return 4;
		}
		size = -1;

	}
	remap_near	= index_remap;
	coord_step_lon	= COORD_STEP; 
	coord_step_lat	= COORD_STEP;
	//*************************************************************************************************



	if ( OUTPUT_UTM == TRUE ){
		printf("Output in UTM proj, conversion of parameters ...\n");

		if ( ( UL_array = (COORD *)malloc(sizeof(COORD)) ) == NULL ){
			printf ("Malloc error UP_array\n");
			return 4;
		}

		i = 0;

		for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){ 
			if ( coordMatrix[1][i] >  180.0 )  coordMatrix[1][i] -= 360.0;
			
		}


		char 		latZone		= getLatZone( coordMatrix[0][i] );
		int  		lonZone 	= getLongZone( coordMatrix[1][i] ); 
		if ( ( matrixLatZone = (char *)malloc(sizeof(char) * pxSizeX * pxSizeY) ) == NULL ){
			printf ("Malloc error matrixLatZone\n");
			return 4;
		}
		if ( ( matrixLonZone = (unsigned char *)malloc(sizeof(unsigned char) * pxSizeX * pxSizeY) ) == NULL ){
			printf ("Malloc error matrixLongZone\n");
			return 4;
		}

		
		UL_array->latZone 	= latZone;
		UL_array->lonZone 	= lonZone;
		UL_array->next		= NULL;

		if ( BBOX == TRUE ){
			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				latZone  	 = ( OUTPUT_UTM_ONLY_LON == TRUE ) ? 'N' : getLatZone(  coordMatrix[0][i] );
				lonZone  	 = getLongZone( coordMatrix[1][i] ); 
				matrixLatZone[i] = latZone;
				matrixLonZone[i] = lonZone;		

				getEasting(coordMatrix[0][i], coordMatrix[1][i], &coordMatrix[1][i], &coordMatrix[0][i]);

				for ( UP_cursor = UL_array; UP_cursor != NULL ; UP_cursor = UP_cursor->next ){ if ( ( UP_cursor->latZone == latZone ) && ( UP_cursor->lonZone == lonZone ) ) break; }
				
				if ( UP_cursor == NULL ){
					for ( UP_cursor = UL_array; UP_cursor->next != NULL ; UP_cursor = UP_cursor->next );
	
					if ( ( UP_cursor->next = (COORD *)malloc(sizeof(COORD)) ) == NULL ){
						printf ("Malloc error UP_array\n");
						return 4;
					}
					UP_cursor 		= UP_cursor->next;
					UP_cursor->latZone 	= latZone;
					UP_cursor->lonZone 	= lonZone;
					UP_cursor->next		= NULL;
				}
			}

		}else{
			
	                UL_array->lat		= FIX_lat;
	                UL_array->lon		= FIX_lon;
			UL_array->latZone	= getLatZone(  UL_array->lat );
			UL_array->lonZone	= getLongZone( UL_array->lon > 180.0 ? UL_array->lon - 180.0 : UL_array->lon );
	                UL_array->next		= NULL;
 
			getEasting( UL_array->lat, UL_array->lon, &UL_array->lon, &UL_array->lat );

			for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
				matrixLatZone[i] = UL_array->latZone;
				matrixLonZone[i] = UL_array->lonZone;		
				latZone  	 = getLatZone(  coordMatrix[0][i] );
				lonZone  	 = getLongZone( coordMatrix[1][i] );

				getEasting(coordMatrix[0][i], coordMatrix[1][i], &coordMatrix[1][i], &coordMatrix[0][i]);



				if ( lonZone >  UL_array->lonZone  ) coordMatrix[1][i] = coordMatrix[1][i] + 500000 * ( lonZone - UL_array->lonZone );

			}

		}

		// writeTestFileByte("matrixLonZone.tif", matrixLonZone, pxSizeX, pxSizeY);
		// writeTestFileDouble("coordMatrix_lon.tif", coordMatrix[1], pxSizeX, pxSizeY);
		// writeTestFileDouble("coordMatrix_lat.tif", coordMatrix[0], pxSizeX, pxSizeY);


		OUTPUT_IN_METERS = TRUE;

		for ( i = 0; pow(10,i) <= floor(dist_avg) ; i++) coord_step_lon = coord_step_lat = pow(10, i );
		if ( coord_step_lon < COORD_STEP ) coord_step_lat = coord_step_lon = COORD_STEP;


		// Check if it's a landast image or another image with resolution already in mgrs
		if ( ( abs(padfGeoTransform[1]) == abs(padfGeoTransform[5]) ) && ( abs(padfGeoTransform[1]) == pow(10, i ) ) ) coord_step_lon = coord_step_lat = pow(10, i );	


		printf("MGRS Pixex size in meters: %dx%d\n", (int)coord_step_lon, (int)coord_step_lat);
	
		if ( MGRS_MODE == TRUE ){
			if ( ( MGRSbuffer = (GByte *)malloc(size * 100 * 100) ) == NULL ){
				printf ("Malloc error MGRSbuffer\n");
				return 4;
			}
		}

		for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ) if ( dist_max[i] < dist_avg) dist_max[i] = ( fabs(coord_step_lon) + fabs(coord_step_lat) ) / 2.0;
		

	}

	if ( CUSTOM_DISTANCE == TRUE ) {
		printf("Use custom max distance: %f ...\n", CUSTOM_DISTANCE_SIZE);
		for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ) dist_max[i] = CUSTOM_DISTANCE_SIZE;
	}

	//*************************************************************************************************


	if( GRID_MODE == FALSE ) printf("Start remapping...\n");
	if( GRID_MODE == TRUE )  printf("Start remapping in Earth Fixed GRID...\n");


	for ( UP_cursor = UL_array; UP_cursor != NULL ; UP_cursor = UP_cursor->next ){
		//if ( ( UP_cursor->lonZone != 60 ) || ( UP_cursor->latZone != 'M' ) ) continue;

		//if ( UP_cursor->lonZone != 32 ) continue;

		// Computation of remap_near (start pixel) in Grid Mode
		if (( UP_cursor != UL_array ) && ( GRID_MODE == TRUE ) ){
			if (( fabs( UP_cursor->prev->lon - UP_cursor->lon ) > (COORD_STEP * WIN_SIZE_X) ) || ( MUST_ONLY_CUT == TRUE ) ) {

	                        GDALApplyGeoTransform(gridGeoTransform, (double)UP_cursor->lon, (double)UP_cursor->lat, &x_near, &y_near);
	                        if ( x_near >= (double)pxSizeX ) x_near = (double)(pxSizeX-1);
	                        if ( x_near < 0.0 )              x_near = 0.0;

	                        if ( y_near >= (double)pxSizeY ) y_near = (double)(pxSizeY-1);
	                        if ( y_near < 0.0)               y_near = 0.0;


	                        remap_near = (int)x_near + ( (int)y_near * pxSizeX );
			}
			
		}

		if ( OUTPUT_UTM == TRUE ){
			// Creation of ROI for UTM zone and search remap_near pixel
			if ( OUTPUT_UTM_ONLY_LON == FALSE ) 	printf("Start remapping zone %d%c ...\n", UP_cursor->lonZone, UP_cursor->latZone);
			else					printf("Start remapping zone %d ...\n",   UP_cursor->lonZone);

			if ( BBOX == TRUE ){

				for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
					if (( matrixLatZone[i] == UP_cursor->latZone) && ( (int)matrixLonZone[i] == UP_cursor->lonZone )){
						MINE = coordMatrix[1][i]; 
						MAXE = coordMatrix[1][i];
						MINN = coordMatrix[0][i];
						MAXN = coordMatrix[0][i];
						remap_near = i;
						break;
					}
				}
	
				for(; i < (pxSizeX * pxSizeY) ; i++ ){
					if (( matrixLatZone[i] == UP_cursor->latZone) && ( (int)matrixLonZone[i] == UP_cursor->lonZone )){
						MINE = ( MINE < coordMatrix[1][i] ) ? MINE : coordMatrix[1][i]; 
						MAXE = ( MAXE > coordMatrix[1][i] ) ? MAXE : coordMatrix[1][i];
						MINN = ( MINN < coordMatrix[0][i] ) ? MINN : coordMatrix[0][i];
						MAXN = ( MAXN > coordMatrix[0][i] ) ? MAXN : coordMatrix[0][i]; 
					}
				}
	
	
				FIX_dist	= sqrt( ( ( MINE - coordMatrix[1][remap_near] ) * ( MINE - coordMatrix[1][remap_near] ) )	+ 
							( ( MAXN - coordMatrix[0][remap_near] ) * ( MAXN - coordMatrix[0][remap_near] ) )	);
	
				for(i = 0 ; i < (pxSizeX * pxSizeY) ; i++ ){
					if (( matrixLatZone[i] == UP_cursor->latZone) && ( (int)matrixLonZone[i] == UP_cursor->lonZone )){
						FIX_new_dist = sqrt( 	( ( MINE - coordMatrix[1][i] ) * ( MINE - coordMatrix[1][i] ) )	+ 
									( ( MAXN - coordMatrix[0][i] ) * ( MAXN - coordMatrix[0][i] ) )	);
	
						if ( FIX_new_dist < FIX_dist ) { FIX_dist = FIX_new_dist; remap_near = i; }
					}
				}


				if ( MGRS_MODE == TRUE ){
					MINE = (double)( (int)( MINE / (coord_step_lon * 100.0) ) * (coord_step_lon * 100.0) );
					MAXN = (double)( (int)( MAXN / (coord_step_lat * 100.0) ) * (coord_step_lat * 100.0) ) - (coord_step_lat * 100.0);
					MAXE = (double)( (int)( MAXE / (coord_step_lon * 100.0) ) * (coord_step_lon * 100.0) ) + (coord_step_lon * 100.0);
					MINN = (double)( (int)( MINN / (coord_step_lat * 100.0) ) * (coord_step_lat * 100.0) );
				}else{
					MINE = (double)( (int)( MINE / coord_step_lon ) * coord_step_lon );
					MAXN = (double)( (int)( MAXN / coord_step_lat ) * coord_step_lat );
					MAXE = (double)( (int)( MAXE / coord_step_lon ) * coord_step_lon );
					MINN = (double)( (int)( MINN / coord_step_lat ) * coord_step_lat );

				}
				

				UP_cursor->lon = MINE; 
				UP_cursor->lat = MAXN;
			}else{
				MINE = UP_cursor->lon;
				MAXN = UP_cursor->lat;


				MAXE = MINE + 1000000;
				MINN = MAXN - 1000000;

			}



			WIN_SIZE_X = (int)( ( MAXE - MINE ) / coord_step_lon );
			WIN_SIZE_Y = (int)( ( MAXN - MINN ) / coord_step_lat );

			if ( ( WIN_SIZE_X <= 0 ) || ( WIN_SIZE_Y <= 0 ) ) {
				printf("Skip this zone... Output size %dx%d ...\n", WIN_SIZE_X, WIN_SIZE_Y);
				continue;
			}

			printf("Output dimention: %dx%d ...\n", WIN_SIZE_X, WIN_SIZE_Y);
			if ( output != NULL ) free(output);
			if ( ( output = (GByte *)malloc(size * WIN_SIZE_X * WIN_SIZE_Y) ) == NULL ){
				printf ("Malloc error output\n");
				return 4;
			}


		}

		FIX_lat		= UP_cursor->lat;
		FIX_lon		= UP_cursor->lon;	
		blank_pix_cnt	= 0;
		x_win 		= ( search_win[0] / 2 );
		y_win 		= ( search_win[1] / 2 );


		// Windows resize in caso of grid mode
		if( GRID_MODE == TRUE ) { 
			if ( MUST_ONLY_CUT == FALSE )	{ x_win = WIN_SIZE_X; y_win = WIN_SIZE_Y; }
			else				{ x_win = 0; y_win = 0; }
		}
		

		//----------------------------------------------------------------------------------------------------------------------


		for ( i = 0 ; i < ( WIN_SIZE_X * WIN_SIZE_Y ) ; i++){ 		

			// Calculate coordinates
			y = (i / WIN_SIZE_X);

		        if (( y % 2 ) == 1 )	x = WIN_SIZE_X - (i % WIN_SIZE_X) - 1;
			else        		x = (i % WIN_SIZE_X);

			x_i = x;
			y_i = y;

			coordRemap[0] = FIX_lat - ( coord_step_lat * y );
			coordRemap[1] = FIX_lon + ( coord_step_lon * x );

	
		        x = ( remap_near % pxSizeX);
		        y = ( remap_near / pxSizeX);
	
			// Up left corner of win
	                x_win_UL = x - x_win;
	                if (x_win_UL < 0 ) x_win_UL = 0;
	                y_win_UL = y - y_win;
	                if (y_win_UL < 0 ) y_win_UL = 0;
	
			// Low Right corner of win
	                x_win_LR = x + x_win;
	                if (x_win_LR >= pxSizeX ) x_win_LR = (pxSizeX-1);
	                y_win_LR = y + y_win;
	                if (y_win_LR >= pxSizeY ) y_win_LR = (pxSizeY-1);
	
			// Init the search near

			if ( ( coordMatrix[0] != NULL ) && ( coordMatrix[1] != NULL ) ){
				i_win =  x_win_UL + ( y_win_UL * pxSizeX );
				if ( OUTPUT_IN_METERS == TRUE ){ // If input is in meters the search in windows is different

					FIX_dist   = sqrt( 	( ( coordRemap[1] - coordMatrix[1][i_win] ) * ( coordRemap[1] - coordMatrix[1][i_win] ) )	+ 
								( ( coordRemap[0] - coordMatrix[0][i_win] ) * ( coordRemap[0] - coordMatrix[0][i_win] ) )	); 

				        for ( j = y_win_UL ; j < y_win_LR+1  ; j++){
					        for ( k = x_win_UL ; k < x_win_LR+1  ; k++){
							i_win =  k + ( j * pxSizeX );
							
							FIX_new_dist = sqrt( 	( ( coordRemap[1] - coordMatrix[1][i_win] ) * ( coordRemap[1] - coordMatrix[1][i_win] ) )	+ 
										( ( coordRemap[0] - coordMatrix[0][i_win] ) * ( coordRemap[0] - coordMatrix[0][i_win] ) )	);

														
	
							if ( FIX_new_dist <= FIX_dist ) {
								if ( ( OUTPUT_UTM == TRUE ) && ( (int)matrixLonZone[i_win] != UP_cursor->lonZone )) continue;
								FIX_dist	= FIX_new_dist;
								remap_near	= i_win;
							}
				                }
				        }


	
		
				}else{	
					FIX_dist =  distAprox( coordRemap[0], coordRemap[1], coordMatrix[0][i_win], coordMatrix[1][i_win] );
				        for ( j = y_win_UL ; j < y_win_LR+1  ; j++){
					        for ( k = x_win_UL ; k < x_win_LR+1  ; k++){
							i_win =  k + ( j * pxSizeX );
							FIX_new_dist = distAprox( coordRemap[0], coordRemap[1] , coordMatrix[0][i_win], coordMatrix[1][i_win] );
						
							if ( FIX_new_dist <= FIX_dist ) {
								FIX_dist	= FIX_new_dist;
								remap_near	= i_win;
							}
				                }
				        }	
				}	

			}else{
			        GDALApplyGeoTransform(gridGeoTransform, (double)coordRemap[1], (double)coordRemap[0], &xdouble, &ydouble);
				FIX_dist = 0.0;
		
	                        if ( xdouble >= (double)pxSizeX ) { xdouble = (double)(pxSizeX-1);	FIX_dist = ( COORD_STEP * 2); }
	                        if ( xdouble < 0.0 )              { xdouble = 0.0;			FIX_dist = ( COORD_STEP * 2); }

	                        if ( ydouble >= (double)pxSizeY ) { ydouble = (double)(pxSizeY-1);	FIX_dist = ( COORD_STEP * 2); }
	                        if ( ydouble < 0.0)               { ydouble = 0.0;			FIX_dist = ( COORD_STEP * 2); }
				
				remap_near = (int)xdouble + ((int)ydouble * pxSizeX);
			}

			if ( 	( OUTPUT_UTM 		== TRUE ) 	&& 
				( OUTPUT_IN_METERS 	== TRUE ) 	&&  
				( ( matrixLatZone[remap_near] != UP_cursor->latZone) || ( (int)matrixLonZone[remap_near] != UP_cursor->lonZone )) ) FIX_dist = dist_max[remap_near] + 1.0;

		        x = ( remap_near % pxSizeX);
		        y = ( remap_near / pxSizeX);

			switch (size){
				case -1:
					matrixRemap[0][x_i + ( y_i * WIN_SIZE_X )] = (unsigned short int)x;
					matrixRemap[1][x_i + ( y_i * WIN_SIZE_X )] = (unsigned short int)y;
					break;

				case 1: // Byte
					if ( FIX_dist < dist_max[remap_near] )	*( output + size * ( x_i + ( y_i * WIN_SIZE_X )))  = *( input + size * ( x + ( y * pxSizeX )) );
					else 					*( output + size * ( x_i + ( y_i * WIN_SIZE_X )))  = (unsigned char)PIXEL_NOT_FOUND;


					if ( *( output + size * ( x_i + ( y_i * WIN_SIZE_X ))) == (unsigned char)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
					break;

				case 2: // short int
					if ( FIX_dist < dist_max[remap_near] )	*(short int *)(output + size*( x_i + ( y_i * WIN_SIZE_X ))) = *(short int *)( input + size * ( x + ( y * pxSizeX )) );
					else					*(short int *)(output + size*( x_i + ( y_i * WIN_SIZE_X ))) = (short int)PIXEL_NOT_FOUND;	

					if ( *(short int *)( output + size * ( x_i + ( y_i * WIN_SIZE_X ))) == (short int)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
					break;
	
				case 4: // int, float
					if ( FIX_dist < dist_max[remap_near] )	*(float *)(output + size*( x_i + ( y_i * WIN_SIZE_X ))) = *(float *)( input + size * ( x + ( y * pxSizeX )) );
					else					*(float *)(output + size*( x_i + ( y_i * WIN_SIZE_X ))) = (float)PIXEL_NOT_FOUND;


					if ( *(float *)( output + size * ( x_i + ( y_i * WIN_SIZE_X ))) == (float)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;

					break;
	
				case 8: // double
					if ( FIX_dist < dist_max[remap_near] )	*(double *)(output + size*( x_i + ( y_i * WIN_SIZE_X ))) = *(double *)( input + size * ( x + ( y * pxSizeX )));
					else					*(double *)(output + size*( x_i + ( y_i * WIN_SIZE_X ))) = (double)PIXEL_NOT_FOUND;		

					if ( *(double *)( output + size * ( x_i + ( y_i * WIN_SIZE_X ))) == (double)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
					break;
	
				default:
					printf("Impossible remap: strange input format...\n");
					return 6;
	
			}
								


			if( GRID_MODE == TRUE ) { 
				if ( MUST_ONLY_CUT == FALSE )	{ x_win = 5; y_win = 5; }
				else{

					if (( y_i % 2 ) == 1 ) 	x_i--;
					else			x_i++;		

					x = (int)x_near + x_i;
					y = (int)y_near + y_i;

					if ( x_i < 0		) { x =  (int)x_near; 			 	y++; }
					if ( x_i >= WIN_SIZE_X 	) { x =  (int)x_near + (WIN_SIZE_X - 1 );	y++; }
		
 					remap_near = x + ( y * pxSizeX);
				}
			}

		}

		//----------------------------------------------------------------------------------------------------------------------

		// -------------------------
		// Create frame for debug
		/*	
		for ( i = 0 ; i < ( WIN_SIZE_X * WIN_SIZE_Y ) ; i++){
                        x = ( i % WIN_SIZE_X);
                        y = ( i / WIN_SIZE_X);
			if (( x == 0 ) || ( x == (WIN_SIZE_X-1))){
				output[i] = 255; 
			}else{
				if (( y == 0 ) || ( y == (WIN_SIZE_Y-1))){
					output[i] = 255; 

				}
			}
		}
		*/
		// -------------------------
	

		// If image is all black skip image creation if flag is set
		if (( BLANK_IMAGE_SKIP == TRUE ) && ( blank_pix_cnt >= ( WIN_SIZE_X * WIN_SIZE_Y ) )) continue; 

		// Calculate zoneid e time-date for output file name
		if( GRID_MODE == TRUE ){
			zoneID = fromLatLongtoZoneId(UP_cursor->lat, UP_cursor->lon, COORD_STEP, WIN_SIZE_X, WIN_SIZE_Y);

			if (( date_start != NULL ) && ( tile_time != NULL )){
				if (	( TRACK_LINE	== TRUE )		&&
					( track_line 	!= NULL )		&& 
					( track_line_x	!= NULL )		&& 
					( track_line_y	!= NULL )		&&
					( track_line_num != 0 ) 		){ // Use track tag to get time like if I use original granule

					// Init search
					k 	 = 0;
					
					if ( (coordMatrix[0] != NULL) && (coordMatrix[1] != NULL) ){
						j 	 = track_line_x[0] + ( track_line_y[0] * pxSizeX );
						FIX_dist = distAprox( UP_cursor->lat, UP_cursor->lon , coordMatrix[0][j], coordMatrix[1][j] );	
					}else{
						GDALApplyGeoTransform(padfGeoTransform, (double)track_line_x[0], (double)track_line_y[0] , &lon, &lat);
						FIX_dist = distAprox( UP_cursor->lat, UP_cursor->lon , lat, lon);
					}


					// Search
					for ( i = 1; i < track_line_num; i++ ){

						if ( (coordMatrix[0] != NULL) && (coordMatrix[1] != NULL) ){
							j		= track_line_x[i] + ( track_line_y[i] * pxSizeX );
							FIX_new_dist	= distAprox( UP_cursor->lat, UP_cursor->lon , coordMatrix[0][j], coordMatrix[1][j] );	
						}else{
							GDALApplyGeoTransform(padfGeoTransform, (double)track_line_x[i], (double)track_line_y[i] , &lon, &lat);
							FIX_new_dist	= distAprox( UP_cursor->lat, UP_cursor->lon , lat, lon);
						}


						if ( FIX_new_dist < FIX_dist ) { 
							FIX_dist        = FIX_new_dist;
							k		= i;
						}
					}
					j = track_line_x[k] + ( track_line_y[k] * pxSizeX );
					getTleTime(date_start, time4line, track_line[k], tile_time);
				}else{
					getTleTime(date_start, time4line, (remap_near / pxSizeX ), tile_time);
				}
			}
		}

		if ( STORE_COORDS == TRUE ){
			printf("Crate output Remapped Matrix ... ");
		        hDstDS = GDALCreate( hDriver, file_out, WIN_SIZE_X, WIN_SIZE_Y, 2, GDT_UInt16,  papszOptions );
		        hBandDst = GDALGetRasterBand( hDstDS, 1 );
	        	GDALRasterIO( hBandDst, GF_Write, 0, 0, WIN_SIZE_X, WIN_SIZE_Y, matrixRemap[0], WIN_SIZE_X, WIN_SIZE_Y, GDT_UInt16, 0, 0);
		        hBandDst = GDALGetRasterBand( hDstDS, 2 );
	        	GDALRasterIO( hBandDst, GF_Write, 0, 0, WIN_SIZE_X, WIN_SIZE_Y, matrixRemap[1], WIN_SIZE_X, WIN_SIZE_Y, GDT_UInt16, 0, 0);
			GDALClose(hDstDS);
			break;

		}	


		// After remapping if longitude is over 180 degree restore original longitude
		// Remove offset for cross date line computation
		if (( OUTPUT_IN_METERS != TRUE ) && ( UP_cursor->lon > 180.0f )) UP_cursor->lon -= 360.0f;	


		
		// if the flag is set create directory tree and generate output file name
		if (( GRID_MODE == TRUE ) && ( TREE_CREATION == TRUE ) && ( RAW_OUTPUT == TRUE ) && ( tile_time != NULL )){
			makeTreeDirectory(file_out, UP_cursor->lat, UP_cursor->lon, tile_time, &file_out_tree);
		}

		if ( RAW_OUTPUT == TRUE ){
			if( GRID_MODE == TRUE ){

				if (file_post != NULL )	sprintf(tmp,"%s%06.*f_%07.*f%s",	file_out, name_tile_decimal, UP_cursor->lat, name_tile_decimal, UP_cursor->lon, file_post);
				else			sprintf(tmp,"%s%06.*f_%07.*f",		file_out, name_tile_decimal, UP_cursor->lat, name_tile_decimal, UP_cursor->lon);
				

				if (date_start != NULL ){
					if (file_out_tree != NULL ){
						if (file_post != NULL )	sprintf(tmp,"%s%s_%07d%s",	file_out_tree, tile_time, zoneID, file_post);
						else			sprintf(tmp,"%s%s_%07d",	file_out_tree, tile_time, zoneID);
					
					}else{
						if (file_post != NULL )	sprintf(tmp,"%s%s_%07d%s",	file_out, tile_time, zoneID, file_post);
						else			sprintf(tmp,"%s%s_%07d",	file_out, tile_time, zoneID);
					}
				}				

				fraw = fopen(tmp, "wb");
			}else{
				printf("Crate output file... ");
				fraw = fopen(file_out, "wb");
			}

		        if(fraw == NULL){
				printf("ERROR: Unable to create output file...\n");
				return 3;
			}
		

			if ( fwrite(output, 1, ( WIN_SIZE_X * WIN_SIZE_Y ), fraw) == 0 ){
				printf("ERROR: write file problem...\n");
				return 3;
			}
			fclose(fraw);
			continue;

		}






		padfGeoTransform[1] = coord_step_lon;		// Pixel X size 
		padfGeoTransform[5] = -coord_step_lat;		// Pixel Y size
		padfGeoTransform[0] = FIX_lon;			// Lon upper left
		padfGeoTransform[3] = FIX_lat; 			// Lat upper left
		padfGeoTransform[2] = padfGeoTransform[4] = 0;	// Rotation zero



		// ----------------------------------------------- //
	
		char    digraph1        = '\0';
		char    digraph2        = '\0';

		int	e_cursor	= 0;
		int	n_cursor	= 0;
		double	e_start		= 0.0;
		double	n_start		= 0.0;
		char    eastingStr[50];
		char    northingStr[50];
		double	MGRSGeoTransform[6] = { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
		

		for ( i = 0; i < 6; i++ ) MGRSGeoTransform[i] = padfGeoTransform[i];
		

		if ( MGRS_MODE == TRUE ){		
			if ( getLatZoneDegree(UP_cursor->latZone) == 'S' ) 	sprintf(tmp,"+proj=utm +zone=%d +datum=WGS84 +units=m +south",	UP_cursor->lonZone);
			else 							sprintf(tmp,"+proj=utm +zone=%d +datum=WGS84 +units=m",		UP_cursor->lonZone);

			OSRSetFromUserInput( hTargetSRS, tmp );
			OSRExportToWkt( hTargetSRS, &pszTargetSRS);


			for (e_cursor = 0; e_cursor < WIN_SIZE_X ; e_cursor += 100.0 ){
				for (n_cursor = 0; n_cursor < WIN_SIZE_Y ; n_cursor += 100.0 ){

					blank_pix_cnt = 0;
					for( i = 0; i< (100 * 100 ); i++){
						x = ( i % 100 ) + e_cursor; y = ( i / 100 ) + n_cursor;
						j = x + ( y * WIN_SIZE_X );

	
						switch (size){
							case 1: // Byte
							*( MGRSbuffer + size * i)  = *( output + size * j );
	
							if ( *( MGRSbuffer + size * i) == (unsigned char)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
							break;
	
						case 2: // short int
							*(short int *)(MGRSbuffer + size * i ) = *(short int *)( output + size * j );

							if ( *( MGRSbuffer + size * i ) == (short int)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
							break;
	
						case 4: // int, float
							*(float *)(MGRSbuffer + size * i ) = *(float *)( output + size * j );
	
							if ( *( MGRSbuffer + size * i ) == (float)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
							break;
		
						case 8: // double
							*(double *)(MGRSbuffer + size * i ) = *(double *)( output + size * j );
		
							if ( *( MGRSbuffer + size * i ) == (double)BLANK_IMAGE_SKIP_VALUE ) blank_pix_cnt++;
							break;
		
						default:
							printf("Impossible remap: strange outptu format...\n");
							return 6;
		
						}
	
					}
	
					if (( BLANK_IMAGE_SKIP == TRUE ) && ( blank_pix_cnt >= ( 100 * 100 ) )) continue; 
	
					e_start = padfGeoTransform[0] + padfGeoTransform[1] * e_cursor;
					n_start = padfGeoTransform[3] + padfGeoTransform[5] * n_cursor;
	
					MGRSGeoTransform[0] = e_start;
					MGRSGeoTransform[3] = n_start;

					digraph1 = getDigraph1( UP_cursor->lonZone, e_start);
					digraph2 = getDigraph2( UP_cursor->lonZone, n_start + 100 * padfGeoTransform[5] );
	
					bzero(eastingStr, 49); bzero(northingStr, 49);
	
					sprintf(eastingStr,     "%d", (int)e_start);
					sprintf(northingStr,    "%d", (int)(n_start + 100 * padfGeoTransform[5]) );
					if ( strlen(eastingStr)  < 5 ) sprintf(eastingStr,      "00000%d", (int)e_start);
					if ( strlen(northingStr) < 5 ) sprintf(northingStr,     "0000%d",  (int)n_start);
					// 4QFJ ................. res 1000m	0 digits
					// 4QFJ16 ............... res 100m	1 digits
					// 4QFJ1267 ............. res 10m	2 digits
					// 4QFJ123678 ........... res 1m	3 digits

		
					if 	( coord_step_lon == 1000.0 ) 	i = 0;
					else if ( coord_step_lon == 100.0  ) 	i = 1;
					else if ( coord_step_lon == 10.0   ) 	i = 2;
					else if ( coord_step_lon == 1.0    ) 	i = 3;
					else					i = 5;

					sprintf(tmp, "%s_%02d%c%c%c%.*s%.*s.tif", file_out, UP_cursor->lonZone, UP_cursor->latZone, digraph1, digraph2,  
									i, eastingStr	+ strlen(eastingStr) 	- 5, 
									i, northingStr 	+ strlen(northingStr) 	- 5);
	
					hDstDS = GDALCreate( hDriver, tmp, 100, 100, 1, type, papszOptions );
				        if(hDstDS == NULL){ printf("ERROR: GDALCreate\n"); return 3; }
	
					if ( GDALSetGeoTransform(hDstDS, MGRSGeoTransform) != CE_None ){
						printf("Transformation coefficients cannot be written\n");
	
					}
	
	
				
					hBandDst = GDALGetRasterBand( hDstDS, 1 );
					GDALRasterIO( hBandDst, GF_Write, 0, 0, 100, 100, MGRSbuffer, 100, 100, type, 0, 0 );
					if ( GDALSetProjection( hDstDS, pszTargetSRS)  != CE_None ){
						printf("Projection reference cannot be written\n");
					}
		
	
					if( hColor != NULL ) GDALSetRasterColorTable( GDALGetRasterBand(hDstDS,1), hColor );
					GDALClose(hDstDS);
	
				}
			}
			continue;
		}
		// ----------------------------------------------- //


		if( GRID_MODE == TRUE ){
			if (file_post != NULL )	sprintf(tmp,"%s%06.*f_%07.*f%s", file_out, name_tile_decimal, UP_cursor->lat, name_tile_decimal, UP_cursor->lon, file_post);
			else			sprintf(tmp,"%s%06.*f_%07.*f",	 file_out, name_tile_decimal, UP_cursor->lat, name_tile_decimal, UP_cursor->lon);

			if (date_start != NULL ){
				if (file_post != NULL )	sprintf(tmp,"%s%s_%07d%s",	file_out, tile_time, zoneID, file_post);
				else			sprintf(tmp,"%s%s_%07d",	file_out, tile_time, zoneID);
			}				


		        hDstDS = GDALCreate( hDriver, tmp, WIN_SIZE_X, WIN_SIZE_Y, 1, type,   papszOptions );

		}else if ( OUTPUT_UTM == TRUE ){
			if ( OUTPUT_UTM_ONLY_LON == FALSE ) 	sprintf(tmp,"%s_%d%c.tif", file_out, UP_cursor->lonZone, UP_cursor->latZone);
			else					sprintf(tmp,"%s_%d.tif",   file_out, UP_cursor->lonZone);

			hDstDS = GDALCreate( hDriver, tmp, WIN_SIZE_X, WIN_SIZE_Y, 1, type,  papszOptions );
			sprintf(tmp, "+proj=utm +zone=%d +datum=WGS84 +units=m", UP_cursor->lonZone);

			OSRSetFromUserInput( hTargetSRS, tmp );
			OSRExportToWkt( hTargetSRS, &pszTargetSRS);


		}else {
			printf("Crate output file... ");
		        hDstDS = GDALCreate( hDriver, file_out, WIN_SIZE_X, WIN_SIZE_Y, 1, type,  papszOptions );
		}

	        if(hDstDS == NULL){
	                printf("ERROR: GDALCreate\n");
	                return 3;
	        }


	
		if( GRID_MODE == FALSE ) printf("Setting GeoTransform... ");
		
		if ( GDALSetGeoTransform(hDstDS, padfGeoTransform) != CE_None ){
			printf("Transformation coefficients cannot be written\n");
	
		}
		


		if ( GRID_MODE == FALSE ) printf("Setting Projection... ");	
		if ( GDALSetProjection( hDstDS, pszTargetSRS)  != CE_None ){
			printf("Projection reference cannot be written\n");
		}
		


		

		if ( ( xpoly != NULL ) && ( ypoly != NULL ) && ( BBOX_GRID == TRUE ) && ( aatsr_mode == TRUE ) && (BBOX == TRUE ) ){
			printf("Setting Meta-Tag for track line... ");
			if ( GDALInvGeoTransform(padfGeoTransform,gridGeoTransform) == FALSE ){
				printf("Problem with inversion of matrix\n");
				return 3;	
			}

			for ( i = 0; i < pxSizeY; i+=3){	
				GDALApplyGeoTransform(gridGeoTransform, xpoly[i], ypoly[i], &x_gcp, &y_gcp);	
				sprintf(track_line_key,"T%d", i);
				sprintf(track_line_value,"%d,%d", (int)x_gcp, (int)y_gcp);
				GDALSetMetadataItem(hDstDS, track_line_key, track_line_value, NULL);
			}
		}



		if( hColor != NULL ){
			GDALSetRasterColorTable( GDALGetRasterBand(hDstDS,1), hColor );
			if ( (GRID_MODE == FALSE) && ( OUTPUT_UTM == FALSE ) ) GDALDestroyColorTable( hColor );
		}

	
	
	        hBandDst = GDALGetRasterBand( hDstDS, 1 );
		if ( GRID_MODE == FALSE ) printf("Write date... ");
	        GDALRasterIO( hBandDst, GF_Write, 0, 0, WIN_SIZE_X, WIN_SIZE_Y, output, WIN_SIZE_X, WIN_SIZE_Y, type, 0, 0);
		if ( GRID_MODE == FALSE ) printf("OK\n");
		GDALClose(hDstDS);
	
	}	
	GDALClose(hSrcDS);
	printf("Done.\n");

	return 0;
}
