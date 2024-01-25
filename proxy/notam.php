<?php
// Dieses Skript liest NOTAMs über eine für maschinelle Anfragen 
// vorgesehene Schnittstelle der Federal Aviation Administration (FAA)
// der USA ein und gibt sie aus.
//
// Kontakt: Markus Sachs, ms@squawk-vfr.de
// Geschrieben für Enroute Flight Navigation im Jan. 2024.
//
// Weitergehende Informationen über die Datenquelle:
// https://www.faa.gov/
//
// Aufruf: [Server/htdocs]/notams.php?locationLongitude=a&locationLatitude=b&radius=c
// mit 
// a = Längengrad (Punkt als Dezimalkomma) des Zentrums der Suche
// b = Breitengrad (Punkt als Dezimalkomma) des Zentrums der Suche
// c = Radius der Suche in [Einheit?]
// Das Anhängen von &pageSize=d mit d als gewünschter Zahl ist optional; 
// ohne Nennung wird 1000 als Default gesetzt.

function isValidLatitude($input) {
    // Define the regular expression pattern for latitude and longitude
    $pattern = '/^(-?\d+(\.\d+)?)$/';

    // Use preg_match to check if the input string matches the pattern
    if (preg_match($pattern, $input) !== 1) {
        return false; // Format is invalid
    }

    // Validate latitude and longitude ranges
    if (!is_numeric($input) || $input < -90 || $input > 90) {
        return false; // Invalid latitude range
    }

    return true; // Input string is valid
}

function isValidLongitude($input) {
    // Define the regular expression pattern for latitude and longitude
    $pattern = '/^(-?\d+(\.\d+)?)$/';

    // Use preg_match to check if the input string matches the pattern
    if (preg_match($pattern, $input) !== 1) {
        return false; // Format is invalid
    }

    // Validate latitude and longitude ranges
    if (!is_numeric($input) || $input < -180 || $input > 180) {
        return false; // Invalid longitude range
    }

    return true; // Input string is valid
}

function isValidRadius($input) {
    // Check if input is numeric and within the range
    return is_numeric($input) && $input > 0 && $input < 500 && intval($input) == $input;
}

function isValidPageSize($input) {
    // Check if input is numeric and within the range
    return is_numeric($input) && $input > 0 && $input <= 1000 && intval($input) == $input;
}




//
// Get parameters and check for validity
//

$pageSize = isset($_GET['pageSize']) ? $_GET['pageSize'] : 1000;
if (!isValidPageSize($pageSize)) die ('Invalid pageSize string!');

if (!isset($_GET['locationLongitude'])) die('No longitude specified'); //FB
$longitude = $_GET['locationLongitude'];
if (!isValidLatitude($longitude)) die ('Invalid longitude string!');

if (!isset($_GET['locationLatitude']))  die('No latitude specified'); //FB
$latitude = $_GET['locationLatitude'];
if (!isValidLatitude($latitude)) die ('Invalid latitude string!');

if (!isset($_GET['locationRadius']))    die('No search radius specified'); //FB
$radius = $_GET['locationRadius'];
if (!isValidLatitude($radius)) die ('Invalid radius string!');


//
// Build request
//

$url = 'https://external-api.faa.gov/notamapi/v1/notams?'
  . 'locationLongitude=' . $longitude
  . '&locationLatitude=' . $latitude
  . '&locationRadius=' . $radius
  . '&pageSize=' . $pageSize;

$FAA_KEY = getenv('FAA_KEY');
$FAA_ID  = getenv('FAA_ID');

$opts = array(
	'http' => array(
		'header' => "client_id: $FAA_ID\r\n" .
		      	    "client_secret: $FAA_KEY\r\n"
	)
);


//
// Get data
//

$context = stream_context_create($opts);
$response = file_get_contents($url, false, $context);


//
// Return data
//

echo $response;
unset($pageSize, $url, $opts, $context, $response);

?>