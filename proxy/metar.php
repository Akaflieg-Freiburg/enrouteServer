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

// Parameter check
if (!isset($_GET['bbox'])) die('Error: bbox definition missing!');
if (!isset($_GET['format'])) die('Error: format definition missing!');

// Get parameter
$bbox   = $_GET['bbox'];
$format = $_GET['format'];

// Build request
$url = "https://aviationweather.gov/api/data/metar?bbox=$bbox&format=$format";

// Get data
$data = file_get_contents($url) OR die('Query incorrect or service not available');

// Return data
echo($data);

?>
