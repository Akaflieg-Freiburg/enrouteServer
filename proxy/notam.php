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

$pageSize = isset($_GET['pageSize']) ? $_GET['pageSize'] : 1000;
if (!isset($_GET['locationLongitude'])) die('No longitude specified'); //FB
if (!isset($_GET['locationLatitude']))  die('No latitude specified'); //FB
if (!isset($_GET['locationRadius']))    die('No search radius specified'); //FB

$url = 'https://external-api.faa.gov/notamapi/v1/notams?locationLongitude=' . $_GET['locationLongitude'] 
	. '&locationLatitude=' . $_GET['locationLatitude'] 
	. '&locationRadius=' . $_GET['locationRadius'] 
	. '&pageSize=' . $pageSize;

$FAA_KEY = getenv('FAA_KEY');
$FAA_ID = getenv('FAA_ID');

	$opts = array(
	'http' => array(
		'header' => "client_id: $FAA_ID\r\n" .
			    "client_secret: $FAA_KEY\r\n"
		)
	);
ob_start(); // direkte Ausgabe abfangen, z.B. bei zu kleinem Radius //FB
$context = stream_context_create($opts);
$response = file_get_contents($url, false, $context);
ob_end_clean(); //FB
if (!strlen($response)) die('ERROR: Failure Contacting Server'); //FB
if (str_contains($response, '"totalCount":0')) die('No NOTAMs found in specified area'); //FB
echo $response;
unset($pageSize, $url, $opts, $context, $response);
?>