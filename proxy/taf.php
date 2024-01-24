<?php
// Dieses Skript liest Wetterdaten über eine für maschinelle
// Anfragen vorgesehene Schnittstelle des Aviation Weather Center (AWC) 
// der USA ein und gibt sie im (gleichen) xml-Format aus.
//
// Kontakt: Markus Sachs, ms@squawk-vfr.de
// Geschrieben für Enroute Flight Navigation im Dez. 2023.
//
// Weitergehende Informationen über die Datenquelle:
// https://aviationweather.gov/ bzw. https://aviationweather.gov/data/api/
//
// Einschränkung des AWC: "Please keep requests limited in scope and frequency."
//
// Aufruf: [Server/htdocs]/get_metar_box.php?box=a,b,c,d&format=e mit 
// a = bottomLeft.latitude
// b = bottomLeft.longitude
// c = topRight.latitude
// d = topRight.longitude
//
// e = desired data format for answer

function isValidBBoxString($input) {
    // Define the regular expression pattern for latitude and longitude
    $pattern = '/^(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)$/';

    // Use preg_match to check if the input string matches the pattern
    if (preg_match($pattern, $input) !== 1) {
        return false; // Format is invalid
    }

    // Split the input string into latitudes and longitudes
    list($lat1, $lon1, $lat2, $lon2) = explode(',', $input);

    // Validate latitude and longitude ranges
    if (!is_numeric($lat1) || $lat1 < -90 || $lat1 > 90 || !is_numeric($lat2) || $lat2 < -90 || $lat2 > 90) {
        return false; // Invalid latitude range
    }

    if (!is_numeric($lon1) || $lon1 < -180 || $lon1 > 180 || !is_numeric($lon2) || $lon2 < -180 || $lon2 > 180) {
        return false; // Invalid longitude range
    }

    return true; // Input string is valid
}

function isValidFormatString($input) {
    // Define the regular expression pattern
    $pattern = '/\b(?:json|xml)\b/';

    // Use preg_match_all to find all occurrences of "json" or "xml" in the input string
    preg_match_all($pattern, $input, $matches);

    // Check if exactly one match is found
    return count($matches[0]) === 1;
}


//
// Get parameter and check for validity
//

if (!isset($_GET['bbox'])) die('Error: bbox definition missing!');
$bbox   = $_GET['bbox'];
if (!isValidBBoxString($bbox)) die('Invalid bounding box string!');

if (!isset($_GET['format'])) die('Error: format definition missing!');
$format = $_GET['format'];
if (!isValidFormatString($format)) die('Invalid format string!');


//
// Build request
//

$url = "https://aviationweather.gov/api/data/taf?bbox=$bbox&format=$format";


//
// Get data
//

$data = file_get_contents($url) OR die('Query incorrect or service not available');


//
// Return data
//
echo($data);

?>
