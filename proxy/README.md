# Proxy Scripts

These are proxy scripts that forward requests from **Enroute Flight Navigation**
to data servers elsewhere (but typically in the United States). The purpose of 
these scripts is that they hide the device IPs from the data servers and thus 
produce an extra layer of privacy.

The scripts are installed in our web servers, so **Enroute Flight Navigation**
knows how to find and use them.

The script "notam.php" assumes that environment variables FAA_ID and FAA_KEY 
contain the credentials required to access the FAA NOTAM service. These can,
for instance, be set with the directive "SetEnv" in Apache's ".htaccess" 
files.

The scripts in this directory were kindly donated by Markus Sachs.
